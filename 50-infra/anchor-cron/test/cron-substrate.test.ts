/**
 * runTickSubstrate orchestration — assert order + arguments + return
 * value with every external surface mocked. No PDS, no L2 RPC.
 */
import {describe, expect, it, vi} from "vitest";

import {
  runTickSubstrate,
  type SubstrateCronConfig,
  type SubstrateCronDeps,
  type SubstratePending,
} from "../src/cron-substrate.js";
import type {SubmitResult} from "../src/submit.js";

const ROOT_CID = "bafymockrootcid";
const ROOT_HASH =
  "0xabcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789" as const;
const TX_HASH =
  "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef" as const;

const CFG: SubstrateCronConfig = {
  contract: "0x1111111111111111111111111111111111111111",
  rpcUrl: "http://localhost:8545",
  signerKey:
    "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
  chainId: 84532,
  pdsUrl: "https://pds.etzhayyim.com",
  pinnerRepo: "did:web:pinner.etzhayyim.com",
  anchorerRepo: "did:web:anchorer.etzhayyim.com",
  confirmations: 1,
  batchMax: 5,
  warnBalanceWei: 0n,
};

function makePending(rootCid: string): SubstratePending {
  return {
    pending: {
      row: {
        cell_did: "com.etzhayyim.apps.threads.post",
        thread_id: rootCid,
        checkpoint_ns: "",
        checkpoint_id: rootCid,
        mst_root_cid: rootCid,
        car_size_bytes: 100,
        car_blob_count: 2,
        mst_projected_at: 0,
        ipfs_pinned_at: 0,
        ipfs_pin_service: "ipfs-pinner",
        ipfs_pin_id: rootCid,
        anchor_tx_hash: null,
        anchor_block_number: null,
        anchor_log_index: null,
        anchor_chain_id: 0,
        anchored_at: null,
      },
      rootHash: ROOT_HASH,
      ipfsCidBytes: new TextEncoder().encode(rootCid),
      batchSize: 3,
    },
    shardKey: "com.etzhayyim.apps.threads.post",
    ipfsPinUri: `at://did:web:pinner.etzhayyim.com/com.etzhayyim.substrate.ipfsPin/3p`,
  };
}

function makeDeps(
  overrides: Partial<SubstrateCronDeps> = {},
): SubstrateCronDeps {
  return {
    readPending: vi.fn(async () => []),
    submitAnchor: vi.fn(
      async (): Promise<SubmitResult> => ({
        txHash: TX_HASH,
        blockNumber: 100,
        logIndex: 0,
        alreadyAnchored: false,
      }),
    ),
    commitL2Anchor: vi.fn(async () => ({uri: "at://x/y/1", cid: "bafyx"})),
    resolveAnchorerAddress: vi.fn(
      async () => "0xC0fFEE000000000000000000000000000000Cafe" as const,
    ),
    checkSolvency: vi.fn(),
    emitSolvencyWarning: vi.fn(),
    log: vi.fn(),
    ...overrides,
  };
}

describe("runTickSubstrate", () => {
  it("returns zero counters when nothing is pending", async () => {
    const deps = makeDeps();
    const out = await runTickSubstrate(CFG, deps);
    expect(out).toEqual({
      freshAnchors: 0,
      alreadyOnChain: 0,
      emittedReceipts: 0,
      solvency: null,
    });
    expect(deps.submitAnchor).not.toHaveBeenCalled();
    expect(deps.commitL2Anchor).not.toHaveBeenCalled();
  });

  it("submits each pending root and commits a receipt back to PDS", async () => {
    const pendingRows = [makePending(ROOT_CID), makePending(ROOT_CID + "2")];
    const deps = makeDeps({
      readPending: vi.fn(async () => pendingRows),
    });
    const out = await runTickSubstrate(CFG, deps);

    expect(deps.submitAnchor).toHaveBeenCalledTimes(2);
    expect(deps.commitL2Anchor).toHaveBeenCalledTimes(2);
    expect(out.freshAnchors).toBe(2);
    expect(out.alreadyOnChain).toBe(0);
    expect(out.emittedReceipts).toBe(2);

    // Receipt body carries shardKey + chainId + ipfsPinUri linkage.
    const firstCommit = (deps.commitL2Anchor as ReturnType<typeof vi.fn>).mock
      .calls[0][0];
    expect(firstCommit.shardKey).toBe("com.etzhayyim.apps.threads.post");
    expect(firstCommit.chainId).toBe(84532);
    expect(firstCommit.ipfsPinUri).toBe(pendingRows[0].ipfsPinUri);
    expect(firstCommit.contract).toBe(CFG.contract);
  });

  it("counts alreadyAnchored separately and still emits a receipt", async () => {
    const deps = makeDeps({
      readPending: vi.fn(async () => [makePending(ROOT_CID)]),
      submitAnchor: vi.fn(
        async (): Promise<SubmitResult> => ({
          txHash: ("0x" + "0".repeat(64)) as `0x${string}`,
          blockNumber: 50,
          logIndex: 0,
          alreadyAnchored: true,
        }),
      ),
    });
    const out = await runTickSubstrate(CFG, deps);
    expect(out.freshAnchors).toBe(0);
    expect(out.alreadyOnChain).toBe(1);
    expect(out.emittedReceipts).toBe(1);
    expect(deps.commitL2Anchor).toHaveBeenCalledTimes(1);
  });

  it("invokes the solvency monitor when warnBalanceWei > 0", async () => {
    const status = {
      address: "0xC0fFEE000000000000000000000000000000Cafe" as `0x${string}`,
      balanceWei: 1000n,
      warnBelowWei: 9999n,
      ok: false,
    };
    const deps = makeDeps({
      checkSolvency: vi.fn(async () => status),
    });
    const out = await runTickSubstrate(
      {...CFG, warnBalanceWei: 9999n},
      deps,
    );
    expect(deps.checkSolvency).toHaveBeenCalledTimes(1);
    expect(deps.emitSolvencyWarning).toHaveBeenCalledWith(status);
    expect(out.solvency).toEqual(status);
  });

  it("swallows solvency RPC failures (anchoring continues)", async () => {
    const deps = makeDeps({
      readPending: vi.fn(async () => [makePending(ROOT_CID)]),
      checkSolvency: vi.fn(async () => {
        throw new Error("rpc-down");
      }),
    });
    const out = await runTickSubstrate(
      {...CFG, warnBalanceWei: 9999n},
      deps,
    );
    expect(out.freshAnchors).toBe(1);
    expect(out.solvency).toBeNull();
    expect(deps.emitSolvencyWarning).not.toHaveBeenCalled();
  });
});
