/**
 * koke rw-free — record types.
 *
 * Per ADR-2605203000 Option B (PDS XRPC). koke = 苔 (moss) — primary
 * fixation actor in the bonsai biology metaphor. Captures raw external
 * signals (CO₂) and fixes them into structured vertices (glucose).
 * Reversible until handoff to hakkou (ferment).
 *
 * Bonsai vascular flow:
 *   koke (fixSignal)  →  hakkou (startFerment)  →  ki (absorb)
 *                                                  → synthesize → bloom
 *
 * Identity hierarchy:
 *   did:web:koke.etzhayyim.com                                — controller
 *   did:web:koke.etzhayyim.com:fixation:{fixationId-slug}     — Fixation
 *   did:web:koke.etzhayyim.com:release:{fixationId}-{seq}     — Release (CO₂)
 */

export const KOKE_DID_PREFIX = "did:web:koke.etzhayyim.com:" as const;

export type SignalKind = "text" | "url" | "record" | "stream";

export interface FixationRecord {
  did: string;
  fixationId: string;
  inputKind: SignalKind;
  rawRef: string;
  /** SHA-256 of the raw signal payload. */
  signalHash: string;
  /** Whether the fixation has been released (CO₂) or still active (glucose). */
  released: boolean;
  agentDid?: string;
  fixedAt: string;
  releasedAt?: string;
  createdAt: string;
}

export interface FixationView extends FixationRecord {
  fixationUri: string;
  vertexId: string;
}

export interface FixSignalInput {
  fixationId: string;
  inputKind: SignalKind;
  rawRef: string;
  signalHash: string;
  agentDid?: string;
}

export interface FixSignalOutput {
  status: "fixed" | "alreadyExists" | "rejected";
  fixationUri?: string;
  vertexId?: string;
  signalHash?: string;
  fixationId?: string;
  error?: string;
}

export interface GetFixationInput {
  fixationId?: string;
}

export interface GetFixationOutput {
  fixation?: FixationView;
  error?: string;
}

export interface ListFixationsInput {
  inputKind?: SignalKind;
  agentDid?: string;
  released?: boolean;
  limit?: number;
  cursor?: string;
}

export interface ListFixationsOutput {
  items: FixationView[];
  cursor?: string;
  total: number;
}

export interface ReleaseCarbonInput {
  fixationId: string;
  reason?: string;
}

export interface ReleaseCarbonOutput {
  status: "released" | "alreadyReleased" | "rejected" | "fixationNotFound";
  fixationUri?: string;
  fixationId?: string;
  releasedAt?: string;
  error?: string;
}

// ─── Slug helpers ───────────────────────────────────────────────────

export function idSlug(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]/g, "-");
}

export function fixationDid(fixationId: string): string {
  return `${KOKE_DID_PREFIX}fixation:${idSlug(fixationId)}`;
}

export function fixationRkey(fixationId: string): string {
  return `fixation-${idSlug(fixationId)}`;
}
