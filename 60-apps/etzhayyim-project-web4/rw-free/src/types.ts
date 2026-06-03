/**
 * web4 rw-free — kotoba-E2E split for the browser-MoE distributed compute
 * marketplace (expert FFN network + Compute Credits).
 *
 * Per ADR-2606011400 (Consensys) + ADR-2605172400 (3-axis) + ADR-2605181100
 * (kotoba E2E encrypted-record envelope). Founder directive 2026-06-03: PII /
 * commercial terms / ledger may migrate to etzhayyim when made safe via kotoba
 * E2E. web4 is one of the named payment apps — front the ledger + balances +
 * tx-history E2E; the fiat-rail execution stays etzhayyim.
 *
 * SPLIT (discriminator: a field is E2E if it carries a person/provider identity,
 * a confidential commercial term, a credit ledger movement, or private request
 * content; pure model/network catalog facts are plaintext):
 *
 *   PUBLIC (plaintext AT records) — open catalog + aggregate market state with
 *   NO party identity:
 *     `modelManifest` — model_id → expert-set catalog (count, quant, total
 *       size). Public model metadata, mirrors S3 manifests/latest.json.
 *     `expert` — pure FFN catalog entry (modelId, expertId, quant, sizeBytes,
 *       blob pointer). FK expert.modelId → modelManifest via exists(). NO
 *       provider DID / device / price ever bleeds here.
 *     `marketStat` — aggregate market snapshot (online providers, active jobs,
 *       median price). DID-free rollup, frontable.
 *
 *   SENSITIVE (kotoba E2E, com.etzhayyim.encrypted.record) — read-cap = owner
 *   DID + explicit recipients; substrate never sees plaintext:
 *     `providerRegistration` — browser GPU provider identity + WebGPU device
 *       fingerprint + two-part price + reputation (per-person PII + commercial
 *       terms).
 *     `inferenceJob` — per-requester job: requester DID + prompt/result content
 *       + assigned provider (private request content). Whole job is E2E so we
 *       never leak requester activity; the federated envelope still fires
 *       subscribeRepos triggers.
 *     `ccLedgerEntry` — Compute Credit ledger movement (credit/debit, balance
 *       after). Tx-history + derivable balance, owner-scoped.
 *
 *   STAYS etzhayyim (consumed via consent-capability, NOT a collection) — the
 *   irreducible regulated EXECUTION:
 *     * GPU/LLM INFERENCE execution itself (browser-worker dispatch + result
 *       compute) — the regulated act, not the resulting job record.
 *     * FIAT on-ramp / merchant-of-record settlement for Compute Credit
 *       purchases (card / bank-wire clearing). etzhayyim never becomes the fiat
 *       counterparty (ADR-2605172100), so the CC ledger DATA migrates E2E but
 *       the fiat-rail settlement CALL stays etzhayyim.
 *     * The 100B-scale S3 expert-weight blob archive (~33MB × expert sets per
 *       model) that physically cannot fit AT PDS; only its manifest/expert
 *       CATALOG metadata fronts plaintext.
 *
 * AT-Lexicon: no float — CC/money/price = decimal STRINGS; sizes/latency/count =
 * integers; reputation/score = integer permille (0-1000) for sub-1% granularity.
 */

// ─── Plaintext public collections ───────────────────────────────────
export const MODEL_MANIFEST_COLLECTION = "com.etzhayyim.apps.web4.modelManifest";
export const EXPERT_COLLECTION = "com.etzhayyim.apps.web4.expert";
export const MARKET_STAT_COLLECTION = "com.etzhayyim.apps.web4.marketStat";

// ─── E2E inner-type NSIDs (body shape inside the encrypted envelope) ──
export const PROVIDER_REGISTRATION_INNER_TYPE = "com.etzhayyim.apps.web4.providerRegistration";
export const INFERENCE_JOB_INNER_TYPE = "com.etzhayyim.apps.web4.inferenceJob";
export const CC_LEDGER_ENTRY_INNER_TYPE = "com.etzhayyim.apps.web4.ccLedgerEntry";

export const WEB4_DID_PREFIX = "did:web:web4.etzhayyim.com:" as const;

// ─── Model manifest (PLAINTEXT, public catalog) ─────────────────────

export interface ModelManifestRecord {
  did: string;
  modelId: string;
  /** number of expert sets, e.g. 32. */
  expertSetCount: number;
  quant: string;
  /** total blob size in bytes (integer, no float). */
  totalSizeBytes: number;
  publishedAt: string;
  createdAt: string;
}
export interface ModelManifestView extends ModelManifestRecord {
  manifestUri: string;
}
export interface RegisterModelManifestInput {
  modelId: string;
  expertSetCount: number;
  quant: string;
  totalSizeBytes: number;
  publishedAt?: string;
}
export interface RegisterModelManifestOutput {
  status: "registered" | "alreadyExists" | "rejected";
  manifestUri?: string;
  did?: string;
  modelId?: string;
  error?: string;
}
export interface ListModelManifestsInput {
  quant?: string;
  limit?: number;
  cursor?: string;
}
export interface ListModelManifestsOutput {
  items: ModelManifestView[];
  cursor?: string;
  total: number;
}

// ─── Expert (PLAINTEXT, FK → modelManifest) ─────────────────────────

export interface ExpertRecord {
  did: string;
  expertKey: string;
  modelId: string;
  /** expert index within the set, e.g. 0..31. */
  expertId: number;
  quant: string;
  /** int4 expert blob size in bytes (integer). */
  sizeBytes: number;
  /** S3 blob path, e.g. models/qwen3-30b-a3b/experts/set-000.bin. */
  blobPath: string;
  createdAt: string;
}
export interface ExpertView extends ExpertRecord {
  expertUri: string;
}
export interface RegisterExpertInput {
  expertKey: string;
  modelId: string;
  expertId: number;
  quant: string;
  sizeBytes: number;
  blobPath: string;
}
export interface RegisterExpertOutput {
  status: "registered" | "alreadyExists" | "rejected";
  expertUri?: string;
  did?: string;
  expertKey?: string;
  error?: string;
}
export interface GetExpertInput {
  expertKey: string;
}
export interface GetExpertOutput {
  expert?: ExpertView;
  error?: string;
}
export interface ListExpertsInput {
  modelId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListExpertsOutput {
  items: ExpertView[];
  cursor?: string;
  total: number;
}

// ─── Market stat (PLAINTEXT, aggregate snapshot, DID-free) ──────────

export interface MarketStatRecord {
  did: string;
  snapshotId: string;
  onlineProviders: number;
  activeJobs: number;
  /** median per-job execution price in CC, decimal string. */
  medianExecPriceCc: string;
  capturedAt: string;
  createdAt: string;
}
export interface MarketStatView extends MarketStatRecord {
  snapshotUri: string;
}
export interface RecordMarketStatInput {
  snapshotId: string;
  onlineProviders: number;
  activeJobs: number;
  medianExecPriceCc: string;
  capturedAt?: string;
}
export interface RecordMarketStatOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  snapshotUri?: string;
  did?: string;
  snapshotId?: string;
  error?: string;
}
export interface ListMarketStatsInput {
  limit?: number;
  cursor?: string;
}
export interface ListMarketStatsOutput {
  items: MarketStatView[];
  cursor?: string;
  total: number;
}

// ─── Provider registration (E2E, PII + commercial terms) ────────────

export interface ProviderRegistrationBody {
  providerKey: string;
  providerDid: string;
  /** WebGPU device fingerprint (e.g. adapter/limits hash). */
  deviceFingerprint: string;
  assignedExpertId: number;
  /** per-minute availability fee in CC, decimal string. */
  availabilityFeeCc: string;
  /** per-job execution fee in CC, decimal string. */
  executionFeeCc: string;
  /** reputation as permille 0-1000 (no float). */
  reputationPermille: number;
  registeredAt: string;
}
export interface ProviderRegistrationView extends ProviderRegistrationBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RegisterProviderInput {
  providerKey: string;
  providerDid: string;
  deviceFingerprint: string;
  assignedExpertId: number;
  availabilityFeeCc: string;
  executionFeeCc: string;
  reputationPermille?: number;
  registeredAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface RegisterProviderOutput {
  status: "registered" | "rejected";
  uri?: string;
  keyId?: string;
  providerKey?: string;
  error?: string;
}
export interface ListProvidersInput {
  assignedExpertId?: number;
  limit?: number;
  cursor?: string;
}
export interface ListProvidersOutput {
  items: ProviderRegistrationView[];
  cursor?: string;
  total: number;
}
export interface GetProviderInput {
  providerKey: string;
}
export interface GetProviderOutput {
  provider?: ProviderRegistrationView;
  error?: string;
}

// ─── Inference job (E2E, private request content) ───────────────────

export interface InferenceJobBody {
  jobId: string;
  requesterDid: string;
  modelId: string;
  /** prompt content (private). */
  prompt: string;
  /** result content, set on completion (private). */
  result?: string;
  assignedProviderKey?: string;
  status: string;
  /** end-to-end latency in milliseconds (integer). */
  latencyMs?: number;
  submittedAt: string;
}
export interface InferenceJobView extends InferenceJobBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface SubmitInferenceInput {
  jobId: string;
  requesterDid: string;
  modelId: string;
  prompt: string;
  result?: string;
  assignedProviderKey?: string;
  status?: string;
  latencyMs?: number;
  submittedAt?: string;
  recipients?: string[];
}
export interface SubmitInferenceOutput {
  status: "submitted" | "rejected";
  uri?: string;
  keyId?: string;
  jobId?: string;
  error?: string;
}
export interface ListJobsInput {
  status?: string;
  limit?: number;
  cursor?: string;
}
export interface ListJobsOutput {
  items: InferenceJobView[];
  cursor?: string;
  total: number;
}
export interface GetJobInput {
  jobId: string;
}
export interface GetJobOutput {
  job?: InferenceJobView;
  error?: string;
}

// ─── CC ledger entry (E2E, ledger movement / tx-history) ────────────

export interface CcLedgerEntryBody {
  entryId: string;
  accountDid: string;
  /** "credit" | "debit". */
  direction: string;
  /** movement amount in CC, decimal string (no float). */
  amountCc: string;
  /** balance after applying this entry, decimal string. */
  balanceAfterCc: string;
  /** "purchase" | "execution" | "availability" | "payout" | "audit". */
  reason: string;
  /** optional linked job/provider key. */
  refKey?: string;
  postedAt: string;
}
export interface CcLedgerEntryView extends CcLedgerEntryBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface PostLedgerEntryInput {
  entryId: string;
  accountDid: string;
  direction: string;
  amountCc: string;
  balanceAfterCc: string;
  reason: string;
  refKey?: string;
  postedAt?: string;
  recipients?: string[];
}
export interface PostLedgerEntryOutput {
  status: "posted" | "rejected";
  uri?: string;
  keyId?: string;
  entryId?: string;
  error?: string;
}
export interface ListLedgerInput {
  accountDid?: string;
  direction?: string;
  limit?: number;
  cursor?: string;
}
export interface ListLedgerOutput {
  items: CcLedgerEntryView[];
  cursor?: string;
  total: number;
}
export interface AccountBalanceInput {
  accountDid: string;
}
export interface AccountBalanceOutput {
  accountDid: string;
  /** latest balanceAfterCc for the account, decimal string. */
  balanceCc?: string;
  entryCount: number;
  error?: string;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  modelManifestCount?: number;
  expertCount?: number;
  marketStatCount?: number;
  providerRegistrationCount?: number;
  inferenceJobCount?: number;
  ccLedgerEntryCount?: number;
  expertsByModel?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
export function isPermille(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0 && n <= 1000;
}
/** decimal money string: non-empty digits with optional single fractional part. */
export function isDecimalString(s: unknown): s is string {
  return typeof s === "string" && /^\d+(\.\d+)?$/.test(s);
}
export function manifestDidFor(id: string): string {
  return `${WEB4_DID_PREFIX}model:${id.toLowerCase()}`;
}
export function slugRkey(prefix: string, id: string): string {
  return `${prefix}-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
