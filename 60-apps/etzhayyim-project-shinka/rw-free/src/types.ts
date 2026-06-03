/**
 * shinka rw-free — Actor Shinka (social-evolution) scheduler, kotoba-E2E split.
 *
 * Per ADR-2606011400 (Consensys product-front / infra-back) + ADR-2605172400
 * (3-axis Liability/Custody/Settlement) + ADR-2605181100 (kotoba E2E encrypted
 * envelope). Founder directive 2026-06-03: PII / CUI / per-person scores migrate
 * to etzhayyim when made E2E-safe.
 *
 * SHINKA DATA SURFACE (from CLAUDE.md + apps/shinka/*.json lexicons):
 *   Historical-propagation scheduler: seedPropagation / generatePropagationChain
 *   produce HistoricalEvent + PropagationEvent + a graph PropagationJob queue
 *   partitioned by era×region (queueStats / listPartitions / listSponsorable).
 *   The per-actor scheduler tracks Joucho 情緒 5-axis scores + mood + kyumei
 *   self-information summaries (forceShinka / stats), driving post/drill cadence.
 *
 * SPLIT:
 *   PUBLIC (plaintext AT records) — historicalEvent catalog: title / era ×
 *   region partition / eventAt / sponsorable flag / propagation fan-out count.
 *   This is open historical reference metadata + aggregate queue structure; no
 *   subject PII. Frontable open catalog (listSponsorable / listPartitions feed
 *   off it). FK: jouchoAssessment.partition references a historicalEvent
 *   partition via exists()-style membership.
 *
 *   SENSITIVE / CUI (kotoba E2E, com.etzhayyim.encrypted.record) —
 *   jouchoAssessment: a named actor's 情緒 5-axis emotional scores (joy / calm /
 *   stress / gratitude / focus), derived mood, and free-text kyumei summary.
 *   These are per-person psychological/cognitive scores (CUI). Sealed via
 *   sdk.encryptedWrite (read-cap = owner DID, auto), so the substrate never sees
 *   an actor's affective profile in plaintext.
 *
 *   STAYS etzhayyim (NOT a collection — consumed via consent-capability) — Murakumo
 *   LLM INFERENCE execution (propagation-chain generation / kyumei drill /
 *   profile repair), credit SPEND + RewardFromCompute SETTLEMENT execution
 *   (yoro.etzhayyim.com/credits), and social-post EXECUTION (postAs actorDid).
 *   These are regulated *acts*; their resulting DATA records migrate (public →
 *   plaintext, per-actor scores → E2E), only the EXECUTION stays etzhayyim.
 *
 * AT-Lexicon: no float. Joucho scores are integer 0-100; fan-out / counts are
 * non-negative integers; sponsor credit is a decimal STRING.
 */

// Plaintext public collection.
export const EVENT_COLLECTION = "com.etzhayyim.apps.shinka.historicalEvent";
// E2E inner-type NSID (body shape inside the encrypted envelope).
export const JOUCHO_INNER_TYPE = "com.etzhayyim.apps.shinka.jouchoAssessment";

export const SHINKA_DID_PREFIX = "did:web:shinka.etzhayyim.com:" as const;

// ─── Historical event (PLAINTEXT, public catalog) ───────────────────

export interface HistoricalEventRecord {
  did: string;
  eventId: string;
  title: string;
  /** era×region partition, e.g. "medieval-asia". */
  partition: string;
  eventAt: string;
  /** propagation chain fan-out size (non-negative integer). */
  propagationCount: number;
  sponsorable: boolean;
  createdAt: string;
}
export interface HistoricalEventView extends HistoricalEventRecord {
  eventUri: string;
}
export interface SeedEventInput {
  eventId: string;
  title: string;
  partition: string;
  eventAt: string;
  propagationCount: number;
  sponsorable?: boolean;
}
export interface SeedEventOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  eventUri?: string;
  did?: string;
  eventId?: string;
  error?: string;
}
export interface ListEventsInput {
  partition?: string;
  sponsorableOnly?: boolean;
  limit?: number;
  cursor?: string;
}
export interface ListEventsOutput {
  items: HistoricalEventView[];
  cursor?: string;
  total: number;
}

// ─── Joucho assessment (E2E-ENCRYPTED, per-actor CUI) ───────────────

export interface JouchoAssessmentBody {
  assessmentId: string;
  actorDid: string;
  /** Must reference a known historicalEvent partition (FK via exists()). */
  partition: string;
  /** integer 0-100 each. */
  joy: number;
  calm: number;
  stress: number;
  gratitude: number;
  focus: number;
  mood: string;
  /** free-text kyumei self-information summary (private). */
  summary: string;
  assessedAt: string;
}
export interface JouchoAssessmentView extends JouchoAssessmentBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordJouchoInput {
  assessmentId: string;
  actorDid: string;
  partition: string;
  joy: number;
  calm: number;
  stress: number;
  gratitude: number;
  focus: number;
  mood: string;
  summary: string;
  assessedAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface RecordJouchoOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  assessmentId?: string;
  error?: string;
}
export interface ListJouchoInput {
  partition?: string;
  mood?: string;
  limit?: number;
  cursor?: string;
}
export interface ListJouchoOutput {
  items: JouchoAssessmentView[];
  cursor?: string;
  total: number;
}
export interface GetJouchoInput {
  assessmentId: string;
}
export interface GetJouchoOutput {
  assessment?: JouchoAssessmentView;
  error?: string;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  historicalEventCount?: number;
  jouchoAssessmentCount?: number;
  eventsByPartition?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
export function isScore(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0 && n <= 100;
}
export function eventDidFor(id: string): string {
  return `${SHINKA_DID_PREFIX}ev:${id.toLowerCase()}`;
}
export function eventRkey(id: string): string {
  return `ev-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
export function jouchoRkey(id: string): string {
  return `joucho-${id.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`;
}
