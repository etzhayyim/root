/**
 * deai rw-free — Spirit-in-Physics matching, kotoba-E2E split.
 *
 * Per ADR-2606011400 (Consensys product-front / infra-back) + ADR-2605172400
 * (3-axis liability/custody/settlement) + ADR-2605181100 (kotoba E2E
 * encrypted-record envelope). Founder directive 2026-06-03: PII / CUI / LE may
 * migrate to etzhayyim when made safe via kotoba E2E.
 *
 * SPLIT (designed from deai's real surface — see CLAUDE.md Data Model):
 *   PUBLIC (plaintext AT records)
 *     - spiritTypeCatalog: the four Jung archetypes (Hero/Sage/Lover/Caregiver)
 *       + complement relation. Pure reference data, frontable open metadata.
 *       complementType is descriptive (the relation is mutual:
 *       Hero↔Caregiver, Sage↔Lover, so it carries no non-circular FK).
 *     - cohortStat: aggregate counts per spirit type (no subject DID, no PII) —
 *       statistical individual-population view, safe to publish. FK-via-exists():
 *       spiritType must reference a registered spiritTypeCatalog entry
 *       (non-circular parent→child edge).
 *   SENSITIVE / PII (kotoba E2E, com.etzhayyim.encrypted.record)
 *     - spiritProfile: actor DID + Hume-derived emotion vector + assigned spirit
 *       type + cohort hash. Biometric-derived per-person data → sealed via
 *       sdk.encryptedWrite (read-cap = owner DID + explicit recipients). The
 *       substrate never sees the emotion vector / actor↔type binding in plain.
 *     - matchScore: per-pair resonance + spirit compatibility between two DIDs.
 *       Confidential per-person scoring → E2E.
 *
 *   STAYS etzhayyim (NOT a collection; consumed via consent-capability) — Hume AI
 *   biometric INFERENCE (face/voice → emotion vector, GPU/LLM execution),
 *   LangGraph deaiMatchEngine score-computation EXECUTION, Vault biometric
 *   custody + Signal DM transport. These are regulated *acts*; the resulting
 *   DATA records migrate (E2E above), only the EXECUTION stays etzhayyim.
 *
 * AT-Lexicon: no float. Reaction time = integer ms. Emotion-vector components +
 * all scores (resonance / compatibility / confidence) = integer 0-100.
 */

// ─── Collection / inner-type NSIDs ──────────────────────────────────

// Plaintext public collections.
export const CATALOG_COLLECTION = "com.etzhayyim.apps.deai.spiritTypeCatalog";
export const COHORT_STAT_COLLECTION = "com.etzhayyim.apps.deai.cohortStat";
// E2E inner-type NSIDs (body shapes inside the encrypted envelope).
export const PROFILE_INNER_TYPE = "com.etzhayyim.apps.deai.spiritProfile";
export const MATCH_INNER_TYPE = "com.etzhayyim.apps.deai.matchScore";

export const DEAI_DID_PREFIX = "did:web:decom.etzhayyim.ai:" as const;

export const SPIRIT_TYPES = ["Hero", "Sage", "Lover", "Caregiver"] as const;
export type SpiritType = (typeof SPIRIT_TYPES)[number];

// ─── Spirit type catalog (PLAINTEXT, public reference data) ─────────

export interface SpiritTypeCatalogRecord {
  did: string;
  spiritType: string;
  /** Jung archetype trait label. */
  traits: string;
  /** Complement archetype (FK → another catalog entry's spiritType). */
  complementType: string;
  createdAt: string;
}
export interface SpiritTypeCatalogView extends SpiritTypeCatalogRecord {
  catalogUri: string;
}
export interface RegisterSpiritTypeInput {
  spiritType: string;
  traits: string;
  complementType: string;
}
export interface RegisterSpiritTypeOutput {
  status: "registered" | "alreadyExists" | "rejected";
  catalogUri?: string;
  did?: string;
  spiritType?: string;
  error?: string;
}
export interface GetSpiritTypeInput {
  spiritType: string;
}
export interface GetSpiritTypeOutput {
  spiritType?: SpiritTypeCatalogView;
  error?: string;
}
export interface ListSpiritTypesInput {
  limit?: number;
  cursor?: string;
}
export interface ListSpiritTypesOutput {
  items: SpiritTypeCatalogView[];
  cursor?: string;
  total: number;
}

// ─── Cohort stat (PLAINTEXT, public aggregate) ──────────────────────

export interface CohortStatRecord {
  did: string;
  statId: string;
  spiritType: string;
  /** Number of (anonymous) participants in this cohort. */
  participantCount: number;
  generatedAt: string;
  createdAt: string;
}
export interface CohortStatView extends CohortStatRecord {
  statUri: string;
}
export interface RecordCohortStatInput {
  statId: string;
  spiritType: string;
  participantCount: number;
  generatedAt?: string;
}
export interface RecordCohortStatOutput {
  status: "recorded" | "alreadyExists" | "rejected";
  statUri?: string;
  did?: string;
  statId?: string;
  error?: string;
}
export interface ListCohortStatsInput {
  spiritType?: string;
  limit?: number;
  cursor?: string;
}
export interface ListCohortStatsOutput {
  items: CohortStatView[];
  cursor?: string;
  total: number;
}

// ─── Spirit profile (E2E-ENCRYPTED, PII / biometric-derived) ────────

export interface SpiritProfileBody {
  profileId: string;
  subjectDid: string;
  spiritType: string;
  cohortHash: string;
  /** Hume 10-dim emotion vector, each component integer 0-100. */
  emotionVector: number[];
  assessedAt: string;
}
export interface SpiritProfileView extends SpiritProfileBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordProfileInput {
  profileId: string;
  subjectDid: string;
  spiritType: string;
  cohortHash: string;
  emotionVector: number[];
  assessedAt?: string;
  /** Extra DIDs to grant read-cap (owner always included). */
  recipients?: string[];
}
export interface RecordProfileOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  profileId?: string;
  error?: string;
}
export interface ListProfilesInput {
  spiritType?: string;
  limit?: number;
  cursor?: string;
}
export interface ListProfilesOutput {
  items: SpiritProfileView[];
  cursor?: string;
  total: number;
}
export interface GetProfileInput {
  profileId: string;
}
export interface GetProfileOutput {
  profile?: SpiritProfileView;
  error?: string;
}

// ─── Match score (E2E-ENCRYPTED, confidential per-pair score) ───────

export interface MatchScoreBody {
  matchId: string;
  subjectDidA: string;
  subjectDidB: string;
  /** integer 0-100. */
  resonanceScore: number;
  /** integer 0-100. */
  spiritCompatibility: number;
  computedAt: string;
}
export interface MatchScoreView extends MatchScoreBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordMatchInput {
  matchId: string;
  subjectDidA: string;
  subjectDidB: string;
  resonanceScore: number;
  spiritCompatibility: number;
  computedAt?: string;
  recipients?: string[];
}
export interface RecordMatchOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  matchId?: string;
  error?: string;
}
export interface ListMatchesInput {
  subjectDid?: string;
  limit?: number;
  cursor?: string;
}
export interface ListMatchesOutput {
  items: MatchScoreView[];
  cursor?: string;
  total: number;
}
export interface GetMatchInput {
  matchId: string;
}
export interface GetMatchOutput {
  match?: MatchScoreView;
  error?: string;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  spiritTypeCatalogCount?: number;
  cohortStatCount?: number;
  spiritProfileCount?: number;
  matchScoreCount?: number;
  statsBySpiritType?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
export function isPct(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0 && n <= 100;
}
export function isPctVector(v: unknown): v is number[] {
  return Array.isArray(v) && v.length > 0 && v.every((x) => isPct(x));
}
export function catalogDidFor(spiritType: string): string {
  return `${DEAI_DID_PREFIX}type:${spiritType.toLowerCase()}`;
}
export function statDidFor(id: string): string {
  return `${DEAI_DID_PREFIX}stat:${id.toLowerCase()}`;
}
export function slug(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}
export function catalogRkey(spiritType: string): string {
  return `type-${slug(spiritType)}`;
}
export function statRkey(id: string): string {
  return `stat-${slug(id)}`;
}
export function profileRkey(id: string): string {
  return `profile-${slug(id)}`;
}
export function matchRkey(id: string): string {
  return `match-${slug(id)}`;
}
