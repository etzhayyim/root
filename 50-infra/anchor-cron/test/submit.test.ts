/**
 * submit — viem walletClient.writeContract contract.
 *
 * Mocked at the viem boundary: `createPublicClient` returns a fake
 * with a single `readContract` (for the idempotency probe);
 * `createWalletClient` returns a fake with `writeContract` +
 * `waitForTransactionReceipt`. We assert on the args passed to those
 * fakes and on the SubmitResult shape returned to anchor-cron's
 * orchestrator.
 */
import {beforeEach, describe, expect, it, vi} from "vitest";

import type {PendingRoot} from "../src/pending.js";

// ── viem mocks (hoisted) ────────────────────────────────────────────

const readContractMock = vi.fn();
const writeContractMock = vi.fn();
const waitForTransactionReceiptMock = vi.fn();
const privateKeyToAccountMock = vi.fn();

vi.mock("viem", async () => {
  return {
    createPublicClient: () => ({
      readContract: readContractMock,
      waitForTransactionReceipt: waitForTransactionReceiptMock,
    }),
    createWalletClient: () => ({writeContract: writeContractMock}),
    http: () => ({}),
    // Pass-through types — the test never inspects them at runtime.
  };
});

vi.mock("viem/accounts", () => ({
  privateKeyToAccount: privateKeyToAccountMock,
}));

// Importing AFTER the mocks above so submit.ts picks them up.
const {submitAnchor, ETZHAYYIM_ANCHOR_ABI} = await import("../src/submit.js");

// ── Fixtures ─────────────────────────────────────────────────────────

const FAKE_CONTRACT = "0xabcdef0123456789abcdef0123456789abcdef01" as `0x${string}`;
const FAKE_KEY =
  "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" as `0x${string}`;

const PENDING: PendingRoot = {
  row: {
    cell_did: "did:test:cell",
    thread_id: "t-1",
    checkpoint_ns: "",
    checkpoint_id: "ckp001",
    mst_root_cid: "bafy-test-cid",
    car_size_bytes: 1024,
    car_blob_count: 0,
    mst_projected_at: Date.now(),
    ipfs_pinned_at: Date.now(),
    ipfs_pin_service: "local-kubo",
    ipfs_pin_id: "bafy-test-cid",
    anchor_tx_hash: null,
    anchor_block_number: null,
    anchor_log_index: null,
    anchor_chain_id: 8453,
    anchored_at: null,
  },
  rootHash: "0xdeadbeef" as `0x${string}`,
  ipfsCidBytes: new Uint8Array([1, 2, 3, 4]),
  batchSize: 1,
};

// Helper to shape the `anchors` mapping return — Solidity tuple-as-array.
function emptyAnchorRow(): readonly [
  `0x${string}`,
  `0x${string}`,
  bigint,
  `0x${string}`,
  bigint,
  bigint,
] {
  return [
    "0x0000000000000000000000000000000000000000000000000000000000000000",
    "0x",
    0n, // blockNumber == 0 → not anchored yet
    "0x0000000000000000000000000000000000000000",
    0n,
    0n,
  ];
}

function anchoredRow(blockNumber: number): readonly [
  `0x${string}`,
  `0x${string}`,
  bigint,
  `0x${string}`,
  bigint,
  bigint,
] {
  return [
    "0x" + "1".repeat(64),
    "0x010203",
    BigInt(blockNumber),
    "0x0000000000000000000000000000000000001234",
    1n,
    1000n,
  ];
}

beforeEach(() => {
  readContractMock.mockReset();
  writeContractMock.mockReset();
  waitForTransactionReceiptMock.mockReset();
  privateKeyToAccountMock.mockReset();
  privateKeyToAccountMock.mockReturnValue({address: "0xfrom"});
});

// ── ABI shape ───────────────────────────────────────────────────────

describe("ETZHAYYIM_ANCHOR_ABI", () => {
  it("declares anchor(bytes32,bytes,uint64)", () => {
    const anchor = ETZHAYYIM_ANCHOR_ABI.find(
      (e) => e.type === "function" && e.name === "anchor",
    );
    expect(anchor).toBeDefined();
    expect(anchor!.inputs.map((i) => i.type)).toEqual([
      "bytes32",
      "bytes",
      "uint64",
    ]);
  });

  it("declares the AlreadyAnchored error so viem can decode it", () => {
    const err = ETZHAYYIM_ANCHOR_ABI.find(
      (e) => e.type === "error" && e.name === "AlreadyAnchored",
    );
    expect(err).toBeDefined();
  });
});

// ── Idempotency probe ───────────────────────────────────────────────

describe("submitAnchor idempotency probe", () => {
  it("short-circuits with alreadyAnchored=true when anchors[rootHash] is populated", async () => {
    readContractMock.mockResolvedValue(anchoredRow(42));

    const res = await submitAnchor({
      contract: FAKE_CONTRACT,
      rpcUrl: "http://localhost:8545",
      signerKey: FAKE_KEY,
      confirmations: 1,
      pending: PENDING,
    });

    expect(readContractMock).toHaveBeenCalledTimes(1);
    expect(readContractMock).toHaveBeenCalledWith(
      expect.objectContaining({
        address: FAKE_CONTRACT,
        functionName: "anchors",
        args: [PENDING.rootHash],
      }),
    );
    // No on-chain tx submitted.
    expect(writeContractMock).not.toHaveBeenCalled();
    expect(waitForTransactionReceiptMock).not.toHaveBeenCalled();

    expect(res.alreadyAnchored).toBe(true);
    expect(res.blockNumber).toBe(42);
    expect(res.logIndex).toBe(0);
    expect(res.txHash).toBe(("0x" + "0".repeat(64)) as `0x${string}`);
  });
});

// ── Fresh anchor path ───────────────────────────────────────────────

describe("submitAnchor fresh-anchor path", () => {
  it("submits anchor(rootHash, ipfsCid bytes, batchSize) when not already on-chain", async () => {
    readContractMock.mockResolvedValue(emptyAnchorRow());
    writeContractMock.mockResolvedValue("0xfeed");
    waitForTransactionReceiptMock.mockResolvedValue({
      blockNumber: 101n,
      logs: [{logIndex: 0}, {logIndex: 1}],
    });

    const res = await submitAnchor({
      contract: FAKE_CONTRACT,
      rpcUrl: "http://localhost:8545",
      signerKey: FAKE_KEY,
      confirmations: 3,
      pending: PENDING,
    });

    expect(writeContractMock).toHaveBeenCalledTimes(1);
    const call = writeContractMock.mock.calls[0][0];
    expect(call.address).toBe(FAKE_CONTRACT);
    expect(call.functionName).toBe("anchor");
    // 0x-hex ipfsCid bytes (length 8 = 4 bytes × 2 hex chars + 0x).
    expect(call.args[0]).toBe(PENDING.rootHash);
    expect(call.args[1]).toBe("0x01020304");
    expect(call.args[2]).toBe(BigInt(PENDING.batchSize));

    expect(waitForTransactionReceiptMock).toHaveBeenCalledWith(
      expect.objectContaining({hash: "0xfeed", confirmations: 3}),
    );

    expect(res.alreadyAnchored).toBe(false);
    expect(res.txHash).toBe("0xfeed");
    expect(res.blockNumber).toBe(101);
    expect(res.logIndex).toBe(0);
  });

  it("logIndex falls back to 0 when receipt logs[] is empty", async () => {
    readContractMock.mockResolvedValue(emptyAnchorRow());
    writeContractMock.mockResolvedValue("0xfeed2");
    waitForTransactionReceiptMock.mockResolvedValue({
      blockNumber: 102n,
      logs: [],
    });

    const res = await submitAnchor({
      contract: FAKE_CONTRACT,
      rpcUrl: "http://localhost:8545",
      signerKey: FAKE_KEY,
      confirmations: 1,
      pending: PENDING,
    });
    expect(res.logIndex).toBe(0);
  });
});
