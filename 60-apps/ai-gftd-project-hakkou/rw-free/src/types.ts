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
