/**
 * ki kotoba — record types.
 *
 * Per ADR-2605203000 Option B (PDS XRPC). ki = 樹液 (sap) — the vascular
 * system of the bonsai actor ecosystem. Carries signals from root
 * absorption (koke/hakkou) up through synthesis (xylem/photosynthesis)
 * and out through phloem distribution (bloom).
 *
 * 4-stage flow (each stage = one lexicon = one PDS record):
 *   absorb     → AbsorbRecord     (raw signal into xylem)
 *   synthesize → SynthesisRecord  (LLM transforms absorb → artifact)
 *   bloom      → BloomRecord      (publish artifact to ecosystem)
 *   ring       → RingRecord       (time-window snapshot, dendrochronology)
 *
 * Note on architecture: ki is a thin-edge dispatcher in vendor — its
 * Worker proxies XRPC calls to dispatcher.etzhayyim.com which then writes to
 * RisingWave. On the etzhayyim substrate, ki's record stream IS the
 * dispatch — the LangServer pod owns the LLM call and writes the
 * SynthesisRecord directly via e.write(). Worker = pure thin facade.
 *
 * Identity hierarchy:
 *   did:web:ki.etzhayyim.com                              — controller
 *   did:web:ki.etzhayyim.com:absorb:{absorbId}            — AbsorbRecord
 *   did:web:ki.etzhayyim.com:synthesis:{artifactId}       — SynthesisRecord
 *   did:web:ki.etzhayyim.com:bloom:{bloomId}              — BloomRecord
 *   did:web:ki.etzhayyim.com:ring:{ringId}                — RingRecord
 */

export const KI_DID_PREFIX = "did:web:ki.etzhayyim.com:" as const;

// ─── Absorb tier ────────────────────────────────────────────────────

export type AbsorbInputKind = "fixation" | "ferment" | "transfer";

export interface AbsorbRecord {
  did: string;
  absorbId: string;
  sourceVertexId: string;
  inputKind: AbsorbInputKind;
  content: string;
  absorbedAt: string;
  createdAt: string;
}

export interface AbsorbView extends AbsorbRecord {
  absorbUri: string;
}

export interface AbsorbInput {
  absorbId: string;
  sourceVertexId: string;
  inputKind: AbsorbInputKind;
  content: string;
}

export interface AbsorbOutput {
  status: "registered" | "alreadyExists" | "rejected";
  absorbUri?: string;
  absorbId?: string;
  did?: string;
  error?: string;
}

// ─── Synthesize tier ────────────────────────────────────────────────

export interface SynthesisRecord {
  did: string;
  artifactId: string;
  absorbId: string;
  /** Synthesized knowledge artifact content (LLM output). */
  synthesis: string;
  /** 0-1000 (permille — AT Lexicon no-float restriction;
   *  lexicon says "0.0-1.0" but uses integer schema so we read it as permille). */
  confidencePermille?: number;
  model?: string;
  synthesizedAt: string;
  createdAt: string;
}

export interface SynthesisView extends SynthesisRecord {
  synthesizeUri: string;
}

export interface SynthesizeInput {
  synthesizeId: string;
  absorbId: string;
  name?: string;
  confidencePermille?: number;
  model?: string;
}

export interface SynthesizeOutput {
  status: "created" | "alreadyExists" | "rejected";
  synthesizeUri?: string;
  artifactId?: string;
  did?: string;
  error?: string;
}

// ─── Bloom tier ─────────────────────────────────────────────────────

export interface BloomRecord {
  did: string;
  bloomId: string;
  artifactId: string;
  publishedAt: string;
  createdAt: string;
}

export interface BloomView extends BloomRecord {
  bloomUri: string;
}

export interface BloomInput {
  bloomId: string;
  synthesizeId: string;
  artifactId?: string;
}

export interface BloomOutput {
  status: "bloomed" | "alreadyExists" | "rejected";
  bloomUri?: string;
  bloomId?: string;
  publishedAt?: string;
  error?: string;
}

// ─── Ring tier ──────────────────────────────────────────────────────

export interface RingRecord {
  did: string;
  ringId: string;
  /** ISO-8601 duration (e.g. PT1H, P1D, P1W). */
  period: string;
  snapshotCount: number;
  snapshotStartAt: string;
  snapshotEndAt: string;
  createdAt: string;
}

export interface RingView extends RingRecord {
  ringUri: string;
}

export interface RingInput {
  ringId: string;
  period: string;
}

export interface RingOutput {
  status: "registered" | "alreadyExists" | "rejected";
  ringUri?: string;
  ringId?: string;
  snapshotCount?: number;
  error?: string;
}

// ─── Slug helpers ───────────────────────────────────────────────────

export function idSlug(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]/g, "-");
}

export function absorbDid(absorbId: string): string {
  return `${KI_DID_PREFIX}absorb:${idSlug(absorbId)}`;
}

export function absorbRkey(absorbId: string): string {
  return `absorb-${idSlug(absorbId)}`;
}

export function synthesisDid(artifactId: string): string {
  return `${KI_DID_PREFIX}synthesis:${idSlug(artifactId)}`;
}

export function synthesisRkey(artifactId: string): string {
  return `synthesis-${idSlug(artifactId)}`;
}

export function bloomDid(bloomId: string): string {
  return `${KI_DID_PREFIX}bloom:${idSlug(bloomId)}`;
}

export function bloomRkey(bloomId: string): string {
  return `bloom-${idSlug(bloomId)}`;
}

export function ringDid(ringId: string): string {
  return `${KI_DID_PREFIX}ring:${idSlug(ringId)}`;
}

export function ringRkey(ringId: string): string {
  return `ring-${idSlug(ringId)}`;
}
