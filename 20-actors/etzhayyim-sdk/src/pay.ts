/**
 * @etzhayyim/sdk/pay — On-chain payment helpers (Base L2 + USDC + ERC-4337).
 *
 * Status: scaffold. Stubs only. See ADR-2605172100.
 *
 * Hard rule: this is the ONLY seam where viem writeContract for value
 * transfer is allowed. App code MUST call Etzhayyim.pay() / .payStream()
 * / .payStreamStop() — direct USDC transfers from app code are prohibited.
 */

// ─── Constants ──────────────────────────────────────────────────────

/** USDC contract on Base L2 (Coinbase Bridged). 6 decimals. */
export const USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" as const;

/** Default Base L2 RPC. */
export const BASE_RPC_DEFAULT = "https://mainnet.base.org" as const;

/** Reserved purpose tags for payment.sent record. */
export type PaymentPurpose =
  | "donation"
  | "tip"
  | "subscription"
  | "purchase"
  | "refund"
  | "grant"
  | "offering"
  | "split";

// ─── Helpers ────────────────────────────────────────────────────────

/**
 * Convert human-readable USDC amount ("10.00") to base units (10000000n).
 * USDC has 6 decimals on Base.
 */
export function parseUsdc(human: string): bigint {
  const [whole, frac = ""] = human.split(".");
  const padded = (frac + "000000").slice(0, 6);
  return BigInt(whole) * 1_000_000n + BigInt(padded || "0");
}

/**
 * Convert "10.00 / month" or "1.00 / day" to USDC base units per second
 * (Superfluid flowRate convention).
 */
export function parseUsdcPerSecond(_perPeriod: string): bigint {
  throw new Error(
    "[etzhayyim-sdk/pay] parseUsdcPerSecond() TODO: parse '<amount> / <month|day|hour|second>', " +
      "convert to base units / second."
  );
}

// ─── One-shot payment ───────────────────────────────────────────────

export interface PayOpts {
  /** Recipient. DID resolved to Smart Wallet address, or raw 0x address. */
  to: string;

  /** Amount in token base units. Use `parseUsdc("10.00")` for USDC. */
  amount: bigint;

  /** Default "USDC". v0.1 only supports USDC on Base. */
  token?: "USDC";

  /** Recorded as the AT payment.sent record body. */
  reason: PaymentReason;

  /**
   * Gas sponsorship. Default "sponsored" = etzhayyim paymaster pays.
   * "user" = user's Smart Wallet pays gas (must have ETH).
   * Address = use this paymaster contract.
   */
  paymaster?: "sponsored" | "user" | `0x${string}`;

  /** Idempotency key. SDK derives one if omitted. */
  idempotencyKey?: string;
}

export interface PaymentReason {
  /** NSID. Default `ai.gftd.apps.payment.sent`. */
  collection?: string;

  /** Purpose tag. */
  purpose: PaymentPurpose;

  /** Optional AT URI of the thing being paid for. */
  forUri?: string;

  /** Optional memo (≤ 280 chars, plaintext). */
  memo?: string;
}

export interface PaymentReceipt {
  /** On-chain tx hash on Base L2. */
  txHash: `0x${string}`;

  /** Block number where the tx was included. */
  blockNumber: bigint;

  /** AT URI of the payment.sent record on the sender's PDS. */
  recordUri: string;

  /** True if the tx was part of an atomic multi-op user-op. */
  atomicBatch: boolean;
}

export async function pay(_opts: PayOpts): Promise<PaymentReceipt> {
  throw new Error(
    "[etzhayyim-sdk/pay] pay() TODO: " +
      "(1) resolve `to` DID → Smart Wallet address, " +
      "(2) build ERC-4337 UserOperation with USDC.transfer(to, amount), " +
      "(3) attach paymaster + signature (passkey → P256), " +
      "(4) submit to Base bundler, await receipt, " +
      "(5) on success, create ai.gftd.apps.payment.sent AT record with txHash, " +
      "(6) enqueue MST root for next L2 anchor batch."
  );
}

// ─── Streaming payment (Superfluid) ─────────────────────────────────

export interface PayStreamOpts {
  /** Recipient (DID or 0x). */
  to: string;

  /** Flow rate in token base units per second. Use `parseUsdcPerSecond`. */
  flowRate: bigint;

  token?: "USDC";

  reason: PaymentReason;

  paymaster?: "sponsored" | "user" | `0x${string}`;
}

export interface StreamHandle {
  /** Superfluid stream identifier (the receiver address as the key). */
  streamId: `0x${string}`;

  /** When the stream started (block timestamp). */
  startedAt: bigint;

  /** AT URI of the payment.streamStarted record. */
  recordUri: string;
}

export async function payStream(_opts: PayStreamOpts): Promise<StreamHandle> {
  throw new Error(
    "[etzhayyim-sdk/pay] payStream() TODO: " +
      "Superfluid Host.callAgreement(CFAv1.createFlow(...)) via ERC-4337 UserOp, " +
      "create ai.gftd.apps.payment.streamStarted record."
  );
}

export async function payStreamStop(_streamId: `0x${string}`): Promise<void> {
  throw new Error(
    "[etzhayyim-sdk/pay] payStreamStop() TODO: " +
      "Superfluid Host.callAgreement(CFAv1.deleteFlow(...)), " +
      "create ai.gftd.apps.payment.streamStopped record."
  );
}

// ─── Escrow (Gnosis Safe) ───────────────────────────────────────────

export interface EscrowOpenOpts {
  to: string;
  amount: bigint;
  token?: "USDC";
  arbiter: `0x${string}`;
  dueDate: Date;
  reason: PaymentReason;
}

export interface EscrowHandle {
  safeAddress: `0x${string}`;
  recordUri: string;
}

export async function escrowOpen(_opts: EscrowOpenOpts): Promise<EscrowHandle> {
  throw new Error(
    "[etzhayyim-sdk/pay] escrowOpen() TODO: deploy Safe 2-of-3 (user/recipient/arbiter), " +
      "fund with USDC, create ai.gftd.apps.payment.escrowOpened record."
  );
}

export async function escrowRelease(
  _safeAddress: `0x${string}`,
  _to: "recipient" | "user"
): Promise<{ txHash: `0x${string}`; recordUri: string }> {
  throw new Error(
    "[etzhayyim-sdk/pay] escrowRelease() TODO: collect 2 signatures, " +
      "execTransaction releasing to recipient (release) or user (refund), " +
      "create ai.gftd.apps.payment.escrowReleased record."
  );
}

// ─── Splits (0xSplits) ──────────────────────────────────────────────

export interface SplitDistributeOpts {
  splitAddress: `0x${string}`;
  amount: bigint;
  token?: "USDC";
  reason: PaymentReason;
}

export async function splitDistribute(_opts: SplitDistributeOpts): Promise<{
  txHash: `0x${string}`;
  recordUri: string;
}> {
  throw new Error(
    "[etzhayyim-sdk/pay] splitDistribute() TODO: send USDC to split contract, " +
      "call distributeERC20(token), create ai.gftd.apps.payment.split record."
  );
}
