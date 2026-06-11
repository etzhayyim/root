/**
 * cron.runTick — orchestration test against fully-mocked deps.
 *
 * No network. No sidecar. Mocks every external surface and asserts on
 * the order + arguments + return-value shape of the loop.
 */
import {beforeEach, describe, expect, it, vi} from "vitest";

import {runTick, type CronConfig, type CronDeps} from "../src/cron.js";
import type {PendingRoot} from "../src/pending.js";
import type {SubmitResult} from "../src/submit.js";
import type {SolvencyStatus} from "../src/solvency.js";

const BASE_CFG: CronConfig = {
  contract: "0x1111111111111111111111111111111111111111",
  rpcUrl: "http://localhost:8545",
  signerKey: "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
  sidecarSocket: "/tmp/etz-test/sidecar.sock",
  cellDids: ["did:test:cellA"],
  confirmations: 1,
  batchMax: 5,
  warnBalanceWei: 0n,
};

function pendingRoot(checkpointId: string, mstCid: string): PendingRoot {
  return {
    row: {
      cell_did: "did:test:cellA",
      thread_id: "t-1",
      checkpoint_ns: "",
      checkpoint_id: checkpointId,
      mst_root_cid: mstCid,
      car_size_bytes: 100,
      car_blob_count: 0,
      mst_projected_at: Date.now(),
      ipfs_pinned_at: Date.now(),
      ipfs_pin_service: "local-kubo",
      ipfs_pin_id: mstCid,
      anchor_tx_hash: null,
      anchor_block_number: null,
      anchor_log_index: null,
      anchor_chain_id: 8453,
      anchored_at: null,
    },
    rootHash: "0xdeadbeef",
    ipfsCidBytes: new TextEncoder().encode(mstCid),
    batchSize: 1,
  };
}

const fresh: SubmitResult = {
  txHash: "0xfeed",
  blockNumber: 100,
  logIndex: 0,
  alreadyAnchored: false,
};
const onChain: SubmitResult = {
  txHash: "0x0000000000000000000000000000000000000000000000000000000000000000",
  blockNumber: 99,
  logIndex: 0,
  alreadyAnchored: true,
};

function makeDeps(overrides: Partial<CronDeps> = {}): CronDeps {
  return {
    health: vi.fn(async () => {}),
    readPending: vi.fn(async () => []),
    submitAnchor: vi.fn(async () => fresh),
    anchorCommit: vi.fn(async () => {}),
    checkSolvency: vi.fn(async () => ({
      signer: "0xsig",
      balanceWei: 5n,
      ok: true,
      warnBelowWei: 1n,
    })),
    emitSolvencyWarning: vi.fn(),
    log: vi.fn(),
    ...overrides,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("runTick", () => {
  it("rejects an empty cellDids list", async () => {
    await expect(
      runTick({...BASE_CFG, cellDids: []}, makeDeps()),
    ).rejects.toThrowError(/cellDids list is empty/);
  });

  it("anchors fresh roots and commits receipts back", async () => {
    const deps = makeDeps({
      readPending: vi
        .fn()
        .mockResolvedValueOnce([
          pendingRoot("ckp1", "bafy-1"),
          pendingRoot("ckp2", "bafy-2"),
        ]),
    });
    const res = await runTick(BASE_CFG, deps);

    expect(deps.health).toHaveBeenCalledWith(BASE_CFG.sidecarSocket);
    expect(deps.readPending).toHaveBeenCalledTimes(1);
    expect(deps.submitAnchor).toHaveBeenCalledTimes(2);
    expect(deps.anchorCommit).toHaveBeenCalledTimes(1);

    const commits = (deps.anchorCommit as ReturnType<typeof vi.fn>).mock
      .calls[0][2];
    expect(commits).toHaveLength(2);
    expect(commits[0]).toMatchObject({
      checkpoint_id: "ckp1",
      anchor_tx_hash: "0xfeed",
      anchor_block_number: 100,
    });
    expect(res.freshAnchors).toBe(2);
    expect(res.alreadyOnChain).toBe(0);
  });

  it("handles already-on-chain results without inflating freshAnchors", async () => {
    const deps = makeDeps({
      readPending: vi
        .fn()
        .mockResolvedValueOnce([pendingRoot("ckp1", "bafy-1")]),
      submitAnchor: vi.fn(async () => onChain),
    });
    const res = await runTick(BASE_CFG, deps);
    expect(res.freshAnchors).toBe(0);
    expect(res.alreadyOnChain).toBe(1);
  });

  it("skips submit + commit when there are no pending rows", async () => {
    const deps = makeDeps({readPending: vi.fn(async () => [])});
    await runTick(BASE_CFG, deps);
    expect(deps.submitAnchor).not.toHaveBeenCalled();
    expect(deps.anchorCommit).not.toHaveBeenCalled();
  });

  it("walks every declared cellDid in order", async () => {
    const deps = makeDeps();
    await runTick(
      {...BASE_CFG, cellDids: ["did:test:a", "did:test:b", "did:test:c"]},
      deps,
    );
    expect(deps.readPending).toHaveBeenCalledTimes(3);
    const cells = (deps.readPending as ReturnType<typeof vi.fn>).mock.calls.map(
      (c) => c[0].cellDid,
    );
    expect(cells).toEqual(["did:test:a", "did:test:b", "did:test:c"]);
  });

  it("calls solvency check + warning when warnBalanceWei > 0", async () => {
    const status: SolvencyStatus = {
      signer: "0xsig",
      balanceWei: 5n,
      ok: false,
      warnBelowWei: 10n,
    };
    const deps = makeDeps({checkSolvency: vi.fn(async () => status)});
    const res = await runTick({...BASE_CFG, warnBalanceWei: 10n}, deps);
    expect(deps.checkSolvency).toHaveBeenCalledTimes(1);
    expect(deps.emitSolvencyWarning).toHaveBeenCalledWith(status);
    expect(res.solvency).toEqual(status);
  });

  it("skips solvency entirely when warnBalanceWei == 0", async () => {
    const deps = makeDeps();
    const res = await runTick(BASE_CFG, deps);
    expect(deps.checkSolvency).not.toHaveBeenCalled();
    expect(deps.emitSolvencyWarning).not.toHaveBeenCalled();
    expect(res.solvency).toBeNull();
  });

  it("does not abort the tick if solvency check throws", async () => {
    const deps = makeDeps({
      checkSolvency: vi.fn(async () => {
        throw new Error("rpc timeout");
      }),
      readPending: vi
        .fn()
        .mockResolvedValueOnce([pendingRoot("ckp1", "bafy-1")]),
    });
    const res = await runTick({...BASE_CFG, warnBalanceWei: 10n}, deps);
    // Anchor flow still ran.
    expect(deps.submitAnchor).toHaveBeenCalledTimes(1);
    expect(res.freshAnchors).toBe(1);
    expect(res.solvency).toBeNull();
    // Log line about the failure was emitted.
    const logs = (deps.log as ReturnType<typeof vi.fn>).mock.calls.map(
      (c) => c[0] as string,
    );
    expect(logs.some((m) => m.includes("solvency: check failed"))).toBe(true);
  });
});
