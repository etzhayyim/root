/**
 * EtzhayyimAnchor.anchor() submission via viem.
 *
 * One on-chain transaction per pending root. Idempotent (the contract
 * reverts with AlreadyAnchored if the same rootHash was anchored before),
 * so a sidecar restart that re-presents a partially-anchored batch is
 * safe — anchor-cron treats AlreadyAnchored as a no-op success and still
 * sends anchor_commit so the sidecar's index catches up.
 */
import {
  createPublicClient,
  createWalletClient,
  http,
  type Address,
  type Hex,
  type PublicClient,
  type WalletClient,
} from "viem";
import {privateKeyToAccount} from "viem/accounts";

import type {PendingRoot} from "./pending.js";

export const ETZHAYYIM_ANCHOR_ABI = [
  {
    type: "function",
    name: "anchor",
    stateMutability: "nonpayable",
    inputs: [
      {name: "rootHash", type: "bytes32"},
      {name: "ipfsCid", type: "bytes"},
      {name: "batchSize", type: "uint64"},
    ],
    outputs: [],
  },
  {
    type: "function",
    name: "anchors",
    stateMutability: "view",
    inputs: [{name: "rootHash", type: "bytes32"}],
    outputs: [
      {name: "rootHash", type: "bytes32"},
      {name: "ipfsCid", type: "bytes"},
      {name: "blockNumber", type: "uint256"},
      {name: "anchorer", type: "address"},
      {name: "batchSize", type: "uint64"},
      {name: "anchoredAt", type: "uint64"},
    ],
  },
  {
    type: "error",
    name: "AlreadyAnchored",
    inputs: [{name: "rootHash", type: "bytes32"}],
  },
  {type: "error", name: "EmptyIpfsCid", inputs: []},
] as const;

export interface SubmitOpts {
  contract: Address;
  rpcUrl: string;
  signerKey: Hex;
  confirmations: number;
  pending: PendingRoot;
}

export interface SubmitResult {
  txHash: `0x${string}`;
  blockNumber: number;
  /** Log index of the Anchored event in the receipt. Falls back to 0 when
   *  the call short-circuited with AlreadyAnchored (no new event). */
  logIndex: number;
  /** True iff this anchor was already on-chain from a prior tick — we
   *  treat it as success and still let the caller anchor_commit. */
  alreadyAnchored: boolean;
}

export async function submitAnchor(opts: SubmitOpts): Promise<SubmitResult> {
  const account = privateKeyToAccount(opts.signerKey);
  const publicClient: PublicClient = createPublicClient({
    transport: http(opts.rpcUrl),
  });
  const walletClient: WalletClient = createWalletClient({
    account,
    transport: http(opts.rpcUrl),
  });

  // Idempotency probe: skip the tx entirely if this rootHash is already
  // anchored. Avoids paying gas to revert on AlreadyAnchored.
  const existing = (await publicClient.readContract({
    address: opts.contract,
    abi: ETZHAYYIM_ANCHOR_ABI,
    functionName: "anchors",
    args: [opts.pending.rootHash],
  })) as readonly [
    `0x${string}`,
    `0x${string}`,
    bigint,
    Address,
    bigint,
    bigint,
  ];
  if (existing[2] !== 0n) {
    // Already on-chain. Surface the pre-existing block number; we don't
    // have the original tx hash without an event scan, so synthesise a
    // marker that the caller can still anchor_commit with.
    return {
      txHash: ("0x" + "0".repeat(64)) as `0x${string}`,
      blockNumber: Number(existing[2]),
      logIndex: 0,
      alreadyAnchored: true,
    };
  }

  const hash = await walletClient.writeContract({
    chain: null,
    account,
    address: opts.contract,
    abi: ETZHAYYIM_ANCHOR_ABI,
    functionName: "anchor",
    args: [
      opts.pending.rootHash,
      ("0x" + bytesToHex(opts.pending.ipfsCidBytes)) as `0x${string}`,
      BigInt(opts.pending.batchSize),
    ],
  });
  const receipt = await publicClient.waitForTransactionReceipt({
    hash,
    confirmations: opts.confirmations,
  });
  return {
    txHash: hash,
    blockNumber: Number(receipt.blockNumber),
    logIndex: receipt.logs[0]?.logIndex ?? 0,
    alreadyAnchored: false,
  };
}

// Local hex helper — anchor-cron stays free of @noble in submit.ts so
// the bundle for the cronjob image is smaller.
function bytesToHex(b: Uint8Array): string {
  let out = "";
  for (let i = 0; i < b.length; i++) out += b[i].toString(16).padStart(2, "0");
  return out;
}
