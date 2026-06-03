/**
 * koke rw-free — record types.
 *
 * Per ADR-2605203000 Option B (PDS XRPC). koke = 苔 (moss) — primary
 * fixation actor in the bonsai biology metaphor. Captures raw external
 * signals (CO₂) and fixes them into structured vertices (glucose).
 * Reversible until handoff to hakkou (ferment).
 *
 * Carbon credit batch management:
 *   registerCarbon  → batchId (idempotent, rkey=batch-{batchId-slug})
 *   releaseCarbon   → releaseId from batchId (idempotent, rkey=release-{releaseId-slug})
 *   recordOffset    → offsetId from releaseId (idempotent, rkey=offset-{offsetId-slug})
 *   listOffsets     → cursor + project filter
 */

export const KOKE_DID_PREFIX = "did:web:koke.etzhayyim.com:" as const;

// ─── Carbon Batch ───────────────────────────────────────────────────

export interface CarbonBatchRecord {
  batchId: string;
  totalCredits: number;
  vintage: number;
  methodology: string;
  createdAt: string;
}

export interface RegisterCarbonInput {
  batchId: string;
  totalCredits: number;
  vintage: number;
  methodology: string;
}

export interface RegisterCarbonOutput {
  status: "created" | "alreadyExists" | "rejected";
  batchUri?: string;
  error?: string;
}

// ─── Release ────────────────────────────────────────────────────────

export interface ReleaseRecord {
  releaseId: string;
  batchId: string;
  releasedCredits: number;
  createdAt: string;
}

export interface ReleaseCarbonInput {
  releaseId: string;
  batchId: string;
  releasedCredits: number;
}

export interface ReleaseCarbonOutput {
  status: "released" | "alreadyReleased" | "rejected";
  releaseUri?: string;
  error?: string;
}

// ─── Offset ─────────────────────────────────────────────────────────

export interface OffsetRecord {
  offsetId: string;
  releaseId: string;
  offsetCredits: number;
  project: string;
  createdAt: string;
}

export interface RecordOffsetInput {
  offsetId: string;
  releaseId: string;
  offsetCredits: number;
  project: string;
}

export interface RecordOffsetOutput {
  status: "recorded" | "alreadyRecorded" | "rejected";
  offsetUri?: string;
  error?: string;
}

export interface ListOffsetsInput {
  project?: string;
  limit?: number;
  cursor?: string;
}

export interface ListOffsetsOutput {
  items: OffsetRecord[];
  cursor?: string;
}

// ─── Slug helpers ───────────────────────────────────────────────────

export function idSlug(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]/g, "-");
}

export function batchRkey(batchId: string): string {
  return `batch-${idSlug(batchId)}`;
}

export function releaseRkey(releaseId: string): string {
  return `release-${idSlug(releaseId)}`;
}

export function offsetRkey(offsetId: string): string {
  return `offset-${idSlug(offsetId)}`;
}
