/**
 * saiban rw-free — public judicial-reference record types.
 *
 * Per ADR-2606011400 (Consensys pattern) — MIXED split. saiban is a judicial
 * intelligence platform. This package migrates its PUBLIC reference layer:
 *   court → judge (FK→court)
 *         → jurisdictionMap (FK→court)
 * Registry on AT PDS records (replaces RW). ADR-2605172000 RW-free.
 *
 * SPLIT NOTE (Custody axis, ADR-2605172400): the `jiken` (case) and `trialEvent`
 * collections carry party PII / confidential litigation (lawfirm-bridged client
 * matters) and STAY etzhayyim / E2E, never public AT records. Only the public judicial
 * reference — courts + judges (public officials) + jurisdiction maps — goes
 * on-substrate.
 *
 * Identity hierarchy:
 *   did:web:saiban.etzhayyim.com                           — controller
 *   did:web:saiban.etzhayyim.com:court:{courtId}           — a court
 *   did:web:saiban.etzhayyim.com:judge:{judgeId}           — a judge
 *   did:web:saiban.etzhayyim.com:jmap:{mappingId}          — a jurisdiction map
 */

export const SAIBAN_DID_PREFIX = "did:web:saiban.etzhayyim.com:" as const;

export const COURT_COLLECTION = "com.etzhayyim.apps.saiban.court";
export const JUDGE_COLLECTION = "com.etzhayyim.apps.saiban.judge";
export const JMAP_COLLECTION = "com.etzhayyim.apps.saiban.jurisdictionMap";

// ─── Court ──────────────────────────────────────────────────────────

export type CourtLevel = "supreme" | "high" | "appellate" | "district" | "family" | "summary" | "other";

export interface CourtRecord {
  did: string;
  courtId: string;
  name: string;
  /** ISO 3166-1 alpha-2 jurisdiction. */
  jurisdiction: string;
  level: CourtLevel;
  parentCourtId?: string;
  createdAt: string;
}
export interface CourtView extends CourtRecord {
  courtUri: string;
}
export interface RegisterCourtInput {
  courtId: string;
  name: string;
  jurisdiction: string;
  level: CourtLevel;
  parentCourtId?: string;
}
export interface RegisterCourtOutput {
  status: "registered" | "alreadyExists" | "rejected" | "parentNotFound";
  courtUri?: string;
  did?: string;
  courtId?: string;
  error?: string;
}
export interface GetCourtInput {
  courtId: string;
}
export interface GetCourtOutput {
  court?: CourtView;
  error?: string;
}
export interface ListCourtsInput {
  jurisdiction?: string;
  level?: CourtLevel;
  parentCourtId?: string;
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListCourtsOutput {
  items: CourtView[];
  cursor?: string;
  total: number;
}

// ─── Judge (public official) ────────────────────────────────────────

export type JudgeTitle = "chief-justice" | "presiding-judge" | "judge" | "associate-judge" | "other";

export interface JudgeRecord {
  did: string;
  judgeId: string;
  /** FK → court courtId. */
  courtId: string;
  name: string;
  title: JudgeTitle;
  appointedDate?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface JudgeView extends JudgeRecord {
  judgeUri: string;
}
export interface AddJudgeInput {
  judgeId: string;
  courtId: string;
  name: string;
  title: JudgeTitle;
  appointedDate?: string;
  sourceUrl?: string;
}
export interface AddJudgeOutput {
  status: "added" | "alreadyExists" | "rejected" | "courtNotFound";
  judgeUri?: string;
  did?: string;
  judgeId?: string;
  error?: string;
}
export interface ListJudgesInput {
  courtId?: string;
  title?: JudgeTitle;
  limit?: number;
  cursor?: string;
}
export interface ListJudgesOutput {
  items: JudgeView[];
  cursor?: string;
  total: number;
}

// ─── Jurisdiction map ───────────────────────────────────────────────

export type MatterType = "civil" | "criminal" | "family" | "administrative" | "bankruptcy" | "other";

export interface JurisdictionMapRecord {
  did: string;
  mappingId: string;
  /** FK → court courtId. */
  courtId: string;
  /** Geographic / subject-matter scope description. */
  scope: string;
  matterType: MatterType;
  createdAt: string;
}
export interface JurisdictionMapView extends JurisdictionMapRecord {
  mappingUri: string;
}
export interface MapJurisdictionInput {
  mappingId: string;
  courtId: string;
  scope: string;
  matterType: MatterType;
}
export interface MapJurisdictionOutput {
  status: "mapped" | "alreadyExists" | "rejected" | "courtNotFound";
  mappingUri?: string;
  did?: string;
  mappingId?: string;
  error?: string;
}
export interface ListJurisdictionMapsInput {
  courtId?: string;
  matterType?: MatterType;
  limit?: number;
  cursor?: string;
}
export interface ListJurisdictionMapsOutput {
  items: JurisdictionMapView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  courtCount?: number;
  judgeCount?: number;
  jurisdictionMapCount?: number;
  courtsByJurisdiction?: Record<string, number>;
  courtsByLevel?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export const LEVELS: ReadonlySet<string> = new Set(["supreme", "high", "appellate", "district", "family", "summary", "other"]);
export const TITLES: ReadonlySet<string> = new Set(["chief-justice", "presiding-judge", "judge", "associate-judge", "other"]);
export const MATTER_TYPES: ReadonlySet<string> = new Set(["civil", "criminal", "family", "administrative", "bankruptcy", "other"]);

export function isJurisdiction(s: string): boolean {
  return /^[A-Z]{2}$/.test(s);
}

export function courtDidFor(id: string): string {
  return `${SAIBAN_DID_PREFIX}court:${id.toLowerCase()}`;
}
export function courtRkey(id: string): string {
  return `court-${id.toLowerCase()}`;
}
export function judgeDidFor(id: string): string {
  return `${SAIBAN_DID_PREFIX}judge:${id.toLowerCase()}`;
}
export function judgeRkey(id: string): string {
  return `judge-${id.toLowerCase()}`;
}
export function jmapDidFor(id: string): string {
  return `${SAIBAN_DID_PREFIX}jmap:${id.toLowerCase()}`;
}
export function jmapRkey(id: string): string {
  return `jmap-${id.toLowerCase()}`;
}
