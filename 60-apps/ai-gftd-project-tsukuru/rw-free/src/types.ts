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

export interface ProductionOrderView extends ProductionOrderRecord {
  productionOrderUri: string;
  updatedAt?: string;
  note?: string;
  updatedByDid?: string;
}

export interface GetOrderInput {
  productionOrderUri: string;
}

export interface GetOrderOutput {
  productionOrder?: ProductionOrderView;
  error?: string;
}

export interface ListOrdersInput {
  manufacturerDid?: string;
  customerDid?: string;
  status?: string;
  limit?: number;
  cursor?: string;
}

export interface ListOrdersOutput {
  items: ProductionOrderView[];
  cursor?: string;
  total: number;
}

export interface UpdateStatusInput {
  productionOrderUri: string;
  status: ProductionOrderStatus;
  note?: string;
  updatedByDid: string;
}

export interface UpdateStatusOutput {
  status: "updated" | "invalidTransition" | "notFound";
  productionOrderUri: string;
  previousStatus?: string;
  newStatus?: string;
  error?: string;
}

/** Allowed forward transitions. cancelled / rejected are terminal. */
export const STATUS_TRANSITIONS: Record<
  ProductionOrderStatus,
  readonly ProductionOrderStatus[]
> = {
  pending: ["accepted", "rejected", "cancelled"],
  accepted: ["material-procurement", "cancelled"],
  "material-procurement": ["in-production", "cancelled"],
  "in-production": ["quality-inspection"],
  "quality-inspection": ["shipped", "in-production"],
  shipped: ["delivered"],
  delivered: [],
  cancelled: [],
  rejected: [],
};

export interface EstimateLeadTimeInput {
  manufacturerDid: string;
  productSpec?: Record<string, unknown>;
  quantity?: number;
  priority?: OrderPriority;
  industryCode?: string;
}

export interface EstimateLeadTimeOutput {
  estimatedDays: number;
  earliestDate: string;
  estimatedCostUsdcMicros?: number;
  industryCode?: string;
  requiredCertifications?: string[];
}

// ─── Quality Inspection ──────────────────────────────────────────────

export type InspectionType = "incoming" | "in-process" | "final" | "audit";
export type InspectionResult =
  | "pass"
  | "conditional_pass"
  | "fail"
  | "rework_required";

/** Results that trigger settlement (escrow_intent → payment.sent). */
export const SETTLEMENT_TRIGGERING_RESULTS = [
  "pass",
  "conditional_pass",
] as const satisfies readonly InspectionResult[];

/** Record body for `ai.gftd.apps.tsukuru.qualityInspection`. */
export interface QualityInspectionRecord {
  productionOrderUri: string;
  inspectorDid: string;
  inspectionType: InspectionType;
  result: InspectionResult;
  defectRatePpm?: number;
  findings?: string[];
  certificationsVerified?: string[];
  lotNumber?: string;
  serialNumbers?: string[];
  paymentSentUri?: string;
  createdAt: string;
}

export interface SubmitInspectionInput {
  productionOrderUri: string;
  inspectorDid: string;
  result: InspectionResult;
  inspectionType?: InspectionType;
  defectRatePpm?: number;
  findings?: string[];
  certificationsVerified?: string[];
  lotNumber?: string;
  serialNumbers?: string[];
}

export interface SubmitInspectionOutput {
  status: "recorded" | "settled" | "settlementFailed";
  inspectionUri: string;
  result: InspectionResult;
  paymentSentUri?: string;
  txHash?: string;
  error?: string;
}

export interface GetInspectionsInput {
  productionOrderUri: string;
  limit?: number;
  cursor?: string;
}

export interface InspectionView extends QualityInspectionRecord {
  inspectionUri: string;
}

export interface GetInspectionsOutput {
  items: InspectionView[];
  cursor?: string;
  total: number;
}

// ─── Manufacturer Registry ───────────────────────────────────────────

export type FactoryType = "oem" | "odm" | "contract" | "in-house";
export type OnboardingStatus =
  | "pending-review"
  | "active"
  | "suspended"
  | "off-boarded";
export type VerificationTier = "basic" | "verified" | "audited";

/** Record body for `ai.gftd.apps.tsukuru.manufacturer`. */
export interface ManufacturerRecord {
  did: string;
  slug: string;
  legalName: string;
  tradeName?: string;
  countryIso3: string;
  isicCodes?: string[];
  category?: string;
  factoryType: FactoryType;
  contactEmail?: string;
  website?: string;
  lei?: string;
  walletAddress?: string;
  verificationTier: VerificationTier;
  onboardingStatus: OnboardingStatus;
  createdAt: string;
}

export interface ManufacturerView extends ManufacturerRecord {
  manufacturerUri: string;
}

export interface RegisterManufacturerInput {
  slug: string;
  legalName: string;
  countryIso3: string;
  tradeName?: string;
  isicCodes?: string[];
  category?: string;
  factoryType?: FactoryType;
  contactEmail?: string;
  website?: string;
  lei?: string;
  walletAddress?: string;
}

export interface RegisterManufacturerOutput {
  status: "registered" | "alreadyExists" | "rejected";
  manufacturerUri?: string;
  did?: string;
  onboardingStatus?: OnboardingStatus;
  error?: string;
}

export interface GetManufacturerInput {
  did?: string;
  slug?: string;
}

export interface GetManufacturerOutput {
  manufacturer?: ManufacturerView;
  error?: string;
}

export interface ListManufacturersInput {
  category?: string;
  countryIso3?: string;
  onboardingStatus?: OnboardingStatus;
  factoryType?: FactoryType;
  limit?: number;
  cursor?: string;
}

export interface ListManufacturersOutput {
  items: ManufacturerView[];
  cursor?: string;
  total: number;
}

export interface SearchManufacturersInput {
  query: string;
  minTier?: VerificationTier;
  isicCode?: string;
  limit?: number;
  cursor?: string;
}

export type SearchManufacturersOutput = ListManufacturersOutput;

export type StatsGroupBy =
  | "countryIso3"
  | "category"
  | "factoryType"
  | "verificationTier"
  | "onboardingStatus";

export interface GetManufacturerStatsInput {
  groupBy?: StatsGroupBy;
}

export interface StatsBucket {
  key: string;
  count: number;
}

export interface GetManufacturerStatsOutput {
  total: number;
  buckets: StatsBucket[];
  groupBy: StatsGroupBy;
  computedAt: string;
}

export const TSUKURU_DID_PREFIX =
  "did:web:tsukuru.etzhayyim.com:manufacturer:" as const;

/** Build a manufacturer DID from a slug. */
export function manufacturerDid(slug: string): string {
  return `${TSUKURU_DID_PREFIX}${slug}`;
}

// ─── Factory Registry ────────────────────────────────────────────────

export type CapacityLevel = "small" | "medium" | "large";

export interface FactoryRecord {
  did: string;
  slug: string;
  manufacturerDid: string;
  factoryName: string;
  countryIso3: string;
  city?: string;
  addressLine?: string;
  postalCode?: string;
  capacityLevel?: CapacityLevel;
  certifications?: string[];
  createdAt: string;
}

export interface FactoryView extends FactoryRecord {
  factoryUri: string;
}

export interface RegisterFactoryInput {
  manufacturerDid: string;
  slug: string;
  factoryName: string;
  countryIso3: string;
  city?: string;
  addressLine?: string;
  postalCode?: string;
  capacityLevel?: CapacityLevel;
  certifications?: string[];
}

export interface RegisterFactoryOutput {
  status: "registered" | "alreadyExists" | "rejected";
  factoryUri?: string;
  did?: string;
  error?: string;
}

export interface ListFactoriesInput {
  manufacturerDid?: string;
  countryIso3?: string;
  limit?: number;
  cursor?: string;
}

export interface ListFactoriesOutput {
  items: FactoryView[];
  cursor?: string;
  total: number;
}

export const FACTORY_DID_PREFIX =
  "did:web:tsukuru.etzhayyim.com:factory:" as const;

export function factoryDid(slug: string): string {
  return `${FACTORY_DID_PREFIX}${slug}`;
}

// ─── Production Progress ─────────────────────────────────────────────

export type Milestone =
  | "material-received"
  | "first-piece"
  | "production-50-percent"
  | "production-100-percent"
  | "inspection-started"
  | "inspection-passed"
  | "packed-for-shipping"
  | "carrier-handoff";

export interface MilestoneRecord {
  productionOrderUri: string;
  milestone: Milestone;
  factoryDid: string;
  note?: string;
  completedPercent?: number;
  evidenceCids?: string[];
  createdAt: string;
}

export interface MilestoneView extends MilestoneRecord {
  milestoneUri: string;
}

export interface ReportMilestoneInput {
  productionOrderUri: string;
  milestone: Milestone;
  factoryDid: string;
  note?: string;
  completedPercent?: number;
  evidenceCids?: string[];
}

export interface ReportMilestoneOutput {
  status: "recorded" | "rejected";
  milestoneUri?: string;
  error?: string;
}

export interface GetProgressInput {
  productionOrderUri: string;
  limit?: number;
  cursor?: string;
}

export interface GetProgressOutput {
  items: MilestoneView[];
  cursor?: string;
  total: number;
}
