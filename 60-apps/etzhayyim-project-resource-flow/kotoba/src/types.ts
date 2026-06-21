/**
 * resource-flow kotoba — public 2次ソース resource-flow visualization data:
 * emitter registry + flow edges + anomaly records.
 *
 * Per ADR-2606011400 (Consensys pattern) + ADR-2605172400 + ADR-0028
 * (gov + private-sector flow) + ADR-0074 (ERC725 root alignment).
 *
 * AXIS NOTE: (c) mixed. resource-flow is a PUBLIC (sensitivity=public) 2次ソース
 * aggregator: gov country apps (gov-jpn/usa/deu/un …), legal-entity DIDs, and
 * cohort actors emit their OWN resource-flow records; this platform receives
 * (follow / subscribeRepos), aggregates, and visualizes them as Sankey diagrams.
 * The flow data is externally-authored public data (external authority = the
 * emitting gov/legal-entity actor), no PII / settlement / liability.
 *   PUBLIC (THIS PACKAGE) — emitter registry + aggregated flow edges + anomaly
 *   records + review state → migrated to etzhayyim front (AT PDS records).
 *   COMPUTE (STAYS etzhayyim) — the anomaly-detection algorithm (BPMN R/PT24H job)
 *   and the sankey-MV aggregation are derived compute, consumed via
 *   consent-capability. Not in this package.
 *
 * AT-Lexicon: no float. Flow amounts are decimal STRINGS (units vary by class).
 *
 * Identity hierarchy:
 *   did:web:resource-flow.etzhayyim.com                      — controller
 *   did:web:resource-flow.etzhayyim.com:flow:{flowId}        — a flow edge
 *   did:web:resource-flow.etzhayyim.com:anom:{anomalyId}     — an anomaly
 */

export const RF_DID_PREFIX = "did:web:resource-flow.etzhayyim.com:" as const;

export const EMITTER_COLLECTION = "com.etzhayyim.apps.resourceFlow.emitter";
export const FLOW_COLLECTION = "com.etzhayyim.apps.resourceFlow.flow";
export const ANOMALY_COLLECTION = "com.etzhayyim.apps.resourceFlow.anomaly";

// ─── Enums ──────────────────────────────────────────────────────────

export type SourceType = "gov" | "legalEntity" | "cohort" | "other";
export type FlowClass =
  | "currency"
  | "service"
  | "personnel"
  | "energy"
  | "material"
  | "information"
  | "goods"
  | "other";
export type Severity = "low" | "medium" | "high" | "critical";
export type ReviewStatus = "open" | "acked" | "dismissed" | "escalated";

export const SOURCE_TYPES: ReadonlySet<string> = new Set(["gov", "legalEntity", "cohort", "other"]);
export const FLOW_CLASSES: ReadonlySet<string> = new Set([
  "currency",
  "service",
  "personnel",
  "energy",
  "material",
  "information",
  "goods",
  "other",
]);
export const SEVERITIES: ReadonlySet<string> = new Set(["low", "medium", "high", "critical"]);
export const REVIEW_STATUSES: ReadonlySet<string> = new Set(["open", "acked", "dismissed", "escalated"]);

// ─── Emitter (registered flow source) ───────────────────────────────

export interface EmitterRecord {
  did: string;
  emitterDid: string;
  label: string;
  sourceType: SourceType;
  flowClasses?: FlowClass[];
  rootDid?: string;
  registeredAt: string;
  createdAt: string;
}
export interface EmitterView extends EmitterRecord {
  emitterUri: string;
}
export interface RegisterEmitterInput {
  emitterDid: string;
  label: string;
  sourceType: SourceType;
  flowClasses?: FlowClass[];
  rootDid?: string;
  registeredAt?: string;
}
export interface RegisterEmitterOutput {
  status: "registered" | "alreadyExists" | "rejected";
  emitterUri?: string;
  did?: string;
  emitterDid?: string;
  error?: string;
}
export interface ListEmittersInput {
  sourceType?: SourceType;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListEmittersOutput {
  items: EmitterView[];
  cursor?: string;
  total: number;
}

// ─── Flow edge (aggregated) ─────────────────────────────────────────

export interface FlowRecord {
  did: string;
  flowId: string;
  flowClass: FlowClass;
  /** FK → emitter (registered source DID). */
  sourceDid: string;
  counterpartyDid: string;
  /** Amount as decimal string (unit varies by flow class). */
  amount: string;
  unit?: string;
  period?: string;
  sourceRootDid?: string;
  counterpartyRootDid?: string;
  observedAt: string;
  createdAt: string;
}
export interface FlowView extends FlowRecord {
  flowUri: string;
}
export interface RecordFlowInput {
  flowId: string;
  flowClass: FlowClass;
  sourceDid: string;
  counterpartyDid: string;
  amount: string;
  observedAt: string;
  unit?: string;
  period?: string;
  sourceRootDid?: string;
  counterpartyRootDid?: string;
}
export interface RecordFlowOutput {
  status: "recorded" | "alreadyExists" | "rejected" | "emitterNotFound";
  flowUri?: string;
  did?: string;
  flowId?: string;
  error?: string;
}
export interface ListFlowsInput {
  flowClass?: FlowClass;
  sourceDid?: string;
  counterpartyDid?: string;
  limit?: number;
  cursor?: string;
}
export interface ListFlowsOutput {
  items: FlowView[];
  cursor?: string;
  total: number;
}

// ─── Anomaly ────────────────────────────────────────────────────────

export interface AnomalyRecord {
  did: string;
  anomalyId: string;
  flowClass: FlowClass;
  /** FK → emitter (source DID the anomaly concerns). */
  sourceDid: string;
  severity: Severity;
  description: string;
  reviewStatus: ReviewStatus;
  detectedAt: string;
  createdAt: string;
}
export interface AnomalyView extends AnomalyRecord {
  anomalyUri: string;
}
export interface RecordAnomalyInput {
  anomalyId: string;
  flowClass: FlowClass;
  sourceDid: string;
  severity: Severity;
  description: string;
  detectedAt: string;
  reviewStatus?: ReviewStatus;
}
export interface RecordAnomalyOutput {
  status: "recorded" | "alreadyExists" | "rejected" | "emitterNotFound";
  anomalyUri?: string;
  did?: string;
  anomalyId?: string;
  error?: string;
}
export interface ReviewAnomalyInput {
  anomalyId: string;
  reviewStatus: ReviewStatus;
}
export interface ReviewAnomalyOutput {
  status: "updated" | "rejected" | "notFound";
  anomalyId?: string;
  newStatus?: ReviewStatus;
  error?: string;
}
export interface ListAnomaliesInput {
  flowClass?: FlowClass;
  sourceDid?: string;
  severity?: Severity;
  reviewStatus?: ReviewStatus;
  limit?: number;
  cursor?: string;
}
export interface ListAnomaliesOutput {
  items: AnomalyView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  emitterCount?: number;
  flowCount?: number;
  anomalyCount?: number;
  flowsByClass?: Record<string, number>;
  anomaliesBySeverity?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUintString(s: string): boolean {
  return /^\d+$/.test(s);
}

export function emitterRkey(did: string): string {
  return `emitter-${did.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
export function flowDidFor(id: string): string {
  return `${RF_DID_PREFIX}flow:${id.toLowerCase()}`;
}
export function flowRkey(id: string): string {
  return `flow-${id.toLowerCase()}`;
}
export function anomalyDidFor(id: string): string {
  return `${RF_DID_PREFIX}anom:${id.toLowerCase()}`;
}
export function anomalyRkey(id: string): string {
  return `anom-${id.toLowerCase()}`;
}
