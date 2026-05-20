/**
 * tsukuru rw-free — record types aligned to Lexicon.
 *
 * Mirrors the tightened lexicons at:
 *   00-contracts/lexicons/ai/gftd/apps/tsukuru/productionOrder/*.json
 *   00-contracts/lexicons/ai/gftd/apps/payment/escrowOpened.json
 *
 * Per ADR-2605202800 Phase 2 — replacing vendor's Stripe Issuing card
 * model + RisingWave vertex_tsukuru_* with on-chain USDC + AT records.
 */

export type FulfillmentMode = "bto" | "mto" | "cto";
export type OrderPriority = "low" | "normal" | "high" | "urgent";
export type PaymentMethod = "escrow_intent" | "direct_pay";

/** Cancellable production-order statuses (pre-delivery). */
export const CANCELLABLE_STATUSES = [
  "pending",
  "accepted",
  "material-procurement",
] as const;
export type CancellableStatus = (typeof CANCELLABLE_STATUSES)[number];

export type ProductionOrderStatus =
  | CancellableStatus
  | "in-production"
  | "quality-inspection"
  | "shipped"
  | "delivered"
  | "cancelled"
  | "rejected";

export interface PaymentIntent {
  method: PaymentMethod;
  amountUsdcMicros: number;
  /** USDC contract on Base L2 by default. */
  tokenContract?: string;
  /** Base L2 mainnet = 8453. */
  chainId?: number;
}

/** Record body for `ai.gftd.apps.tsukuru.productionOrder.productionOrder`. */
export interface ProductionOrderRecord {
  manufacturerDid: string;
  customerDid: string;
  factoryDid?: string;
  productSpec: Record<string, unknown>;
  fulfillmentMode: FulfillmentMode;
  priority: OrderPriority;
  deadline?: string;
  payment?: PaymentIntent;
  okaimonoOrderRef?: string;
  certificationsRequired?: string[];
  status: ProductionOrderStatus;
  estimatedCompletion?: string;
  estimatedDays?: number;
  escrowIntentUri?: string;
  paymentSentUri?: string;
  escrowRefundUri?: string;
  createdAt: string;
  cancelledAt?: string;
  cancelReason?: string;
  cancelledByDid?: string;
}

/** Record body for `ai.gftd.apps.payment.escrowOpened` — Gnosis Safe 2-of-3.
 *  Phase 2 intent-only: safeAddress + arbiter are placeholders until SDK
 *  v0.2 implements escrowOpen() per ADR-2605202900. */
export interface EscrowOpenedRecord {
  to: string;
  amountUsdcMicros: number;
  tokenContract: string;
  chainId: number;
  safeAddress: string;
  arbiter: string;
  dueDate: string;
  purpose: "purchase" | "grant" | "subscription";
  forUri?: string;
  memo?: string;
  openedAt: string;
}

/** Refund record — Phase 2 record-only state transition (no on-chain tx).
 *  Lexicon to-be-added: ai.gftd.apps.payment.escrowRefunded. */
export interface EscrowRefundedRecord {
  forEscrowUri: string;
  forProductionOrderUri: string;
  reason: string;
  refundedAt: string;
  refundedByDid: string;
  /** Phase 2: empty (no on-chain tx since escrow_intent never settled).
   *  Phase 2b+ when SDK escrowRelease lands: populated with refund tx hash. */
  refundTxHash?: string;
}

export interface CreateOrderInput {
  manufacturerDid: string;
  customerDid: string;
  factoryDid?: string;
  productSpec: Record<string, unknown>;
  fulfillmentMode?: FulfillmentMode;
  priority?: OrderPriority;
  deadline?: string;
  payment?: PaymentIntent;
  okaimonoOrderRef?: string;
  certificationsRequired?: string[];
}

export interface CreateOrderOutput {
  productionOrderUri: string;
  status: "pending" | "rejected";
  escrowIntentUri?: string;
  estimatedCompletion?: string;
  estimatedDays?: number;
  manufacturerDid?: string;
  error?: string;
}

export interface CancelOrderInput {
  productionOrderUri: string;
  reason?: string;
  cancelledByDid?: string;
}

export interface CancelOrderOutput {
  status: "cancelled" | "cannotCancel";
  productionOrderUri: string;
  escrowRefundUri?: string;
  currentStatus?: string;
  cancellableStatuses?: string[];
  error?: string;
}
