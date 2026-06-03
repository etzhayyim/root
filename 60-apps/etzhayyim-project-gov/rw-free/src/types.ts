/**
 * gov rw-free — public government reference record types.
 *
 * Per ADR-2606011400 (Consensys pattern) — MIXED split. gov is a public-services
 * Well-Becoming hub. This package migrates its PUBLIC reference layer:
 *   - agency       — government agencies (COFOG-aligned)
 *   - official     — public officials (public-disclosure data)
 *   - municipality — administrative units
 * Registry on AT PDS records (replaces RW). ADR-2605172000 RW-free.
 *
 * SPLIT NOTE (Custody axis, ADR-2605172400): `submitConsult` / the consult
 * collection — citizen consultations on healthcare / welfare / education — can
 * carry sensitive personal-situation PII and STAYS etzhayyim infra (consent-
 * capability), never on public records. Only public government open-data
 * (agencies / officials / municipalities) goes on-substrate.
 *
 * AT-Lexicon: no float. Population is an integer.
 *
 * Identity hierarchy:
 *   did:web:gov.etzhayyim.com                              — controller
 *   did:web:gov.etzhayyim.com:agency:{agencyId}            — an agency
 *   did:web:gov.etzhayyim.com:official:{officialId}        — a public official
 *   did:web:gov.etzhayyim.com:muni:{municipalityId}        — a municipality
 */

export const GOV_DID_PREFIX = "did:web:gov.etzhayyim.com:" as const;

export const AGENCY_COLLECTION = "com.etzhayyim.apps.gov.agency";
export const OFFICIAL_COLLECTION = "com.etzhayyim.apps.gov.official";
export const MUNICIPALITY_COLLECTION = "com.etzhayyim.apps.gov.municipality";

// ─── Agency ─────────────────────────────────────────────────────────

export type GovLevel = "national" | "prefectural" | "municipal";

export interface AgencyRecord {
  did: string;
  agencyId: string;
  name: string;
  level: GovLevel;
  /** COFOG function code (e.g. "07" health), optional. */
  cofogCode?: string;
  /** Parent agency (hierarchy), optional. */
  parentAgencyId?: string;
  region?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface AgencyView extends AgencyRecord {
  agencyUri: string;
}
export interface RegisterAgencyInput {
  agencyId: string;
  name: string;
  level: GovLevel;
  cofogCode?: string;
  parentAgencyId?: string;
  region?: string;
  sourceUrl?: string;
}
export interface RegisterAgencyOutput {
  status: "registered" | "alreadyExists" | "rejected" | "parentNotFound";
  agencyUri?: string;
  did?: string;
  agencyId?: string;
  error?: string;
}
export interface GetAgencyInput {
  agencyId: string;
}
export interface GetAgencyOutput {
  agency?: AgencyView;
  error?: string;
}
export interface ListAgenciesInput {
  level?: GovLevel;
  cofogCode?: string;
  region?: string;
  parentAgencyId?: string;
  /** App-layer substring match over name. */
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListAgenciesOutput {
  items: AgencyView[];
  cursor?: string;
  total: number;
}

// ─── Official ───────────────────────────────────────────────────────

export interface OfficialRecord {
  did: string;
  officialId: string;
  /** FK → agency agencyId. */
  agencyId: string;
  name: string;
  title: string;
  /** Term, e.g. "2024–2028", optional. */
  term?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface OfficialView extends OfficialRecord {
  officialUri: string;
}
export interface RecordOfficialInput {
  officialId: string;
  agencyId: string;
  name: string;
  title: string;
  term?: string;
  sourceUrl?: string;
}
export interface RecordOfficialOutput {
  status: "recorded" | "alreadyExists" | "rejected" | "agencyNotFound";
  officialUri?: string;
  did?: string;
  officialId?: string;
  error?: string;
}
export interface ListOfficialsInput {
  agencyId?: string;
  title?: string;
  limit?: number;
  cursor?: string;
}
export interface ListOfficialsOutput {
  items: OfficialView[];
  cursor?: string;
  total: number;
}

// ─── Municipality ───────────────────────────────────────────────────

export interface MunicipalityRecord {
  did: string;
  municipalityId: string;
  name: string;
  prefecture: string;
  /** 5-digit JIS municipality code, optional. */
  jisCode?: string;
  /** Population (integer), optional. */
  population?: number;
  createdAt: string;
}
export interface MunicipalityView extends MunicipalityRecord {
  municipalityUri: string;
}
export interface RegisterMunicipalityInput {
  municipalityId: string;
  name: string;
  prefecture: string;
  jisCode?: string;
  population?: number;
}
export interface RegisterMunicipalityOutput {
  status: "registered" | "alreadyExists" | "rejected";
  municipalityUri?: string;
  did?: string;
  municipalityId?: string;
  error?: string;
}
export interface ListMunicipalitiesInput {
  prefecture?: string;
  limit?: number;
  cursor?: string;
}
export interface ListMunicipalitiesOutput {
  items: MunicipalityView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  agencyCount?: number;
  officialCount?: number;
  municipalityCount?: number;
  agenciesByLevel?: Record<string, number>;
  totalPopulation?: number;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export const LEVELS: ReadonlySet<string> = new Set(["national", "prefectural", "municipal"]);

export function isNonNegInt(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}

export function agencyDidFor(id: string): string {
  return `${GOV_DID_PREFIX}agency:${id.toLowerCase()}`;
}
export function agencyRkey(id: string): string {
  return `agency-${id.toLowerCase()}`;
}
export function officialDidFor(id: string): string {
  return `${GOV_DID_PREFIX}official:${id.toLowerCase()}`;
}
export function officialRkey(id: string): string {
  return `official-${id.toLowerCase()}`;
}
export function municipalityDidFor(id: string): string {
  return `${GOV_DID_PREFIX}muni:${id.toLowerCase()}`;
}
export function municipalityRkey(id: string): string {
  return `muni-${id.toLowerCase()}`;
}
