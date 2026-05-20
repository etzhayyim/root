/**
 * hanrei rw-free — record types.
 *
 * Japanese case-law corpus. Per ADR-2605203000 Option B (PDS XRPC).
 * Replaces vendor's vertex_hanrei_jurisdiction / vertex_hanrei_court /
 * vertex_hanrei_case_record with AT PDS records.
 *
 * Identity hierarchy (per hanrei CLAUDE.md):
 *   did:web:hanrei.etzhayyim.com                       — controller
 *   did:web:hanrei.etzhayyim.com:jurisdiction:{iso3}   — country / region
 *   did:web:hanrei.etzhayyim.com:court:{jurisdiction}:{courtId}
 *   did:web:hanrei.etzhayyim.com:case:{caseId}
 *   did:web:hanrei.etzhayyim.com:law:{lawId}
 */

export interface JurisdictionRecord {
  did: string;
  iso3: string;
  name: string;
  nameLocal?: string;
  legalSystem?: "civil-law" | "common-law" | "religious-law" | "mixed";
  courts?: string[];
  primaryLanguage?: string;
  caseLawSource?: string;
  createdAt: string;
}

export interface JurisdictionView extends JurisdictionRecord {
  jurisdictionUri: string;
}

export interface RegisterJurisdictionInput {
  iso3: string;
  name: string;
  nameLocal?: string;
  legalSystem?: JurisdictionRecord["legalSystem"];
  courts?: string[];
  primaryLanguage?: string;
  caseLawSource?: string;
}

export interface RegisterJurisdictionOutput {
  status: "registered" | "alreadyExists" | "rejected";
  jurisdictionUri?: string;
  did?: string;
  iso3?: string;
  error?: string;
}

export interface GetJurisdictionInput {
  iso3: string;
}

export interface GetJurisdictionOutput {
  jurisdiction?: JurisdictionView;
  error?: string;
}

export interface ListJurisdictionsInput {
  legalSystem?: JurisdictionRecord["legalSystem"];
  limit?: number;
  cursor?: string;
}

export interface ListJurisdictionsOutput {
  items: JurisdictionView[];
  cursor?: string;
  total: number;
}

export const HANREI_DID_PREFIX = "did:web:hanrei.etzhayyim.com:" as const;

export function jurisdictionDid(iso3: string): string {
  return `${HANREI_DID_PREFIX}jurisdiction:${iso3.toLowerCase()}`;
}

export function jurisdictionRkey(iso3: string): string {
  return `jurisdiction-${iso3.toLowerCase()}`;
}

// ─── Court tier (slice 2) ───────────────────────────────────────────

export type CourtTier =
  | "supreme"
  | "high"
  | "ip-high"
  | "district"
  | "family"
  | "summary";

export interface CourtRecord {
  did: string;
  jurisdiction: string;
  courtId: string;
  name: string;
  nameLocal?: string;
  tier?: CourtTier;
  role?: string;
  searchPath?: string;
  createdAt: string;
}

export interface CourtView extends CourtRecord {
  courtUri: string;
}

export interface CourtProfileInput {
  courtId: string;
  name: string;
  nameLocal?: string;
  tier?: CourtTier;
  role?: string;
  searchPath?: string;
}

export interface RegisterCourtProfilesInput {
  jurisdiction: string;
  courts: CourtProfileInput[];
}

export interface RegisterCourtProfilesOutput {
  status: "ok" | "rejected";
  jurisdiction?: string;
  registered?: { courtId: string; courtUri: string; did: string }[];
  skipped?: { courtId: string; reason: string }[];
  error?: string;
}

export interface ListCourtsInput {
  jurisdiction?: string;
  tier?: CourtTier;
  limit?: number;
  cursor?: string;
}

export interface ListCourtsOutput {
  items: CourtView[];
  cursor?: string;
  total: number;
}

export interface CollectWikidataCourtsInput {
  jurisdiction?: string;
}

export interface CollectWikidataCourtsOutput {
  status: "ok";
  schema: string;
  source: string;
  sparqlEndpoint: string;
  jurisdiction?: string;
  collected: number;
  inserted: number;
  skipped: number;
  collectedAt: string;
}

// ─── Case tier (slice 3) ────────────────────────────────────────────

export interface CaseRecord {
  did: string;
  caseId: string;
  title: string;
  courtDid?: string;
  jurisdiction?: string;
  decidedAt?: string;
  caseNumber?: string;
  summary?: string;
  tags?: string[];
  sourceUrl?: string;
  createdAt: string;
}

export interface CaseView extends CaseRecord {
  caseUri: string;
}

export interface CaseSeedInput {
  caseId: string;
  title: string;
  courtDid?: string;
  jurisdiction?: string;
  decidedAt?: string;
  caseNumber?: string;
  summary?: string;
  tags?: string[];
  sourceUrl?: string;
}

export interface SeedCasesInput {
  cases: CaseSeedInput[];
}

export interface SeedCasesOutput {
  status: "ok" | "rejected";
  inserted?: { caseId: string; caseUri: string }[];
  skipped?: { caseId: string; reason: string }[];
  error?: string;
}

export interface GetCaseInput {
  caseId?: string;
}

export interface GetCaseOutput {
  case?: CaseView;
  error?: string;
}

export interface ListCasesInput {
  courtDid?: string;
  jurisdiction?: string;
  limit?: number;
  cursor?: string;
}

export interface ListCasesOutput {
  items: CaseView[];
  cursor?: string;
  total: number;
}

export interface SearchCasesInput {
  query: string;
  courtDid?: string;
  limit?: number;
  cursor?: string;
}

export type SearchCasesOutput = ListCasesOutput;

// ─── Law tier (slice 4) ─────────────────────────────────────────────

export type LawStatus = "in-force" | "amended" | "repealed" | "proposed";

export interface LawRecord {
  did: string;
  lawId: string;
  title: string;
  titleLocal?: string;
  jurisdiction?: string;
  enactedAt?: string;
  effectiveAt?: string;
  repealedAt?: string;
  status?: LawStatus;
  sourceUrl?: string;
  tags?: string[];
  createdAt: string;
}

export interface LawView extends LawRecord {
  lawUri: string;
}

export interface RegisterLawInput {
  lawId: string;
  title: string;
  titleLocal?: string;
  jurisdiction?: string;
  enactedAt?: string;
  effectiveAt?: string;
  repealedAt?: string;
  status?: LawStatus;
  sourceUrl?: string;
  tags?: string[];
}

export interface RegisterLawOutput {
  status: "registered" | "alreadyExists" | "rejected";
  lawUri?: string;
  did?: string;
  lawId?: string;
  error?: string;
}

export interface GetLawInput {
  lawId?: string;
}

export interface GetLawOutput {
  law?: LawView;
  error?: string;
}

export interface ListLawsInput {
  jurisdiction?: string;
  status?: LawStatus;
  limit?: number;
  cursor?: string;
}

export interface ListLawsOutput {
  items: LawView[];
  cursor?: string;
  total: number;
}
