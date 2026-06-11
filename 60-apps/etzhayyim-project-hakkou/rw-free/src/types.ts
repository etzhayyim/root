/**
 * hakkou rw-free — record types.
 *
 * Per ADR-2605203000 Option B (PDS XRPC). hakkou = 発酵 (fermentation)
 * — irreversible transformation of fixed signals (glucose) into
 * structured knowledge (ethanol) + audit trail (CO₂). Consumes koke
 * fixations and emits to ki absorb tier.
 *
 * Bonsai vascular flow:
 *   koke (fixSignal)  →  hakkou (startFerment)  →  ki (absorb)
 *
 * Identity hierarchy:
 *   did:web:hakkou.etzhayyim.com                                — controller
 *   did:web:hakkou.etzhayyim.com:ferment:{fermentId-slug}       — FermentRun
 */

export const HAKKOU_DID_PREFIX = "did:web:hakkou.etzhayyim.com:" as const;

export type FermentInputKind = "text" | "record" | "stream";

export type FermentOutputKind =
  | "summary"
  | "embedding"
  | "graph-fragment"
  | "classification";

export type FermentStatus = "pending" | "running" | "done" | "failed";

export interface FermentRunRecord {
  did: string;
  fermentId: string;
  agentDid: string;
  inputKind: FermentInputKind;
  inputRef: string;
  outputKind: FermentOutputKind;
  status: FermentStatus;
  /** Reference to the koke fixation this ferment was triggered from. */
  sourceFixationDid?: string;
  resultRef?: string;
  startedAt: string;
  completedAt?: string;
  failedAt?: string;
  errorReason?: string;
  createdAt: string;
}

export interface FermentRunView extends FermentRunRecord {
  fermentUri: string;
  fermentVertexId: string;
}

export interface StartFermentInput {
  fermentId: string;
  agentDid: string;
  inputKind: FermentInputKind;
  inputRef: string;
  outputKind: FermentOutputKind;
  sourceFixationDid?: string;
}

export interface StartFermentOutput {
  status: "started" | "alreadyExists" | "rejected";
  fermentVertexId?: string;
  fermentId?: string;
  fermentUri?: string;
  error?: string;
}

export interface GetFermentInput {
  fermentId?: string;
}

export interface GetFermentOutput {
  ferment?: FermentRunView;
  error?: string;
}

/** Helper: update an existing ferment to a new status (transition). */
export interface UpdateFermentStatusInput {
  fermentId: string;
  status: FermentStatus;
  resultRef?: string;
  errorReason?: string;
}

export interface UpdateFermentStatusOutput {
  status: "updated" | "rejected" | "fermentNotFound";
  fermentUri?: string;
  fermentId?: string;
  newStatus?: FermentStatus;
  error?: string;
}

// ─── Slug helpers ───────────────────────────────────────────────────

export function idSlug(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]/g, "-");
}

export function fermentDid(fermentId: string): string {
  return `${HAKKOU_DID_PREFIX}ferment:${idSlug(fermentId)}`;
}

export function fermentRkey(fermentId: string): string {
  return `ferment-${idSlug(fermentId)}`;
}

// ─── Batch types ───────────────────────────────────────────────────

export type BatchType = "sake" | "miso" | "koji" | "vinegar";

export type BatchStatus = "pending" | "running" | "done" | "failed";

export interface BatchRecord {
  did: string;
  batchId: string;
  batchType: BatchType;
  startDate: string;
  targetEndDate: string;
  status: BatchStatus;
  createdAt: string;
}

export interface BatchView extends BatchRecord {
  batchUri: string;
  batchVertexId: string;
}

export interface RegisterBatchInput {
  batchId: string;
  batchType: BatchType;
  startDate: string;
  targetEndDate: string;
}

export interface RegisterBatchOutput {
  status: "created" | "alreadyExists" | "rejected";
  batchUri?: string;
  batchId?: string;
  error?: string;
}

export interface GetBatchInput {
  batchId: string;
}

export interface GetBatchOutput {
  batch?: BatchView;
  error?: string;
}

export interface ListBatchesInput {
  batchType?: BatchType;
}

export interface ListBatchesOutput {
  items: BatchView[];
}

export interface UpdateBatchStatusInput {
  statusUpdateId: string;
  batchId: string;
  newStatus: BatchStatus;
}

export interface UpdateBatchStatusOutput {
  status: "updated" | "rejected";
  previousStatus?: BatchStatus;
  newStatus?: BatchStatus;
  error?: string;
}

export function batchDid(batchId: string): string {
  return `did:web:hakkou.etzhayyim.com:batch:${idSlug(batchId)}`;
}

export function batchRkey(batchId: string): string {
  return `batch-${idSlug(batchId)}`;
}
