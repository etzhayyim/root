/**
 * seibutsu (生物) kotoba — biodiversity taxonomy open-data record types.
 *
 * Per ADR-2606011400 (Consensys pattern) + ADR-2605172400 (3-axis OR-test).
 *
 * AXIS NOTE: (a) axis-clean public open-data — biodiversity taxonomy follows
 * the GBIF / iNaturalist model: taxa, procedural traits, and citizen-science
 * sightings are PUBLIC reference data. No settlement, no PII custody, no
 * fulfillment liability. The `identify` image→species capability (Murakumo
 * fleet inference) is AI COMPUTE and stays etzhayyim; the catalog itself migrates.
 *
 * PII posture: observer is a PUBLIC contributor-handle attribution (iNaturalist-
 * style), not raw personal data. Sighting geo is coarsened to an H3 cell (never
 * precise GPS — protects endangered-species localities). No raw PII on substrate.
 *
 * AT-Lexicon: no float. Heights/lifespans are integers (cm / years). The
 * Linnaean hierarchy is an edge-only self-ref (parentTaxonId FK→taxon); records
 * do not nest.
 *
 * Identity hierarchy:
 *   did:web:seibutsu.etzhayyim.com                       — controller
 *   did:web:seibutsu.etzhayyim.com:taxon:{taxonId}       — a taxon
 *   did:web:seibutsu.etzhayyim.com:traits:{traitId}      — a procedural profile
 *   did:web:seibutsu.etzhayyim.com:obs:{observationId}   — a sighting
 */

export const SEIBUTSU_DID_PREFIX = "did:web:seibutsu.etzhayyim.com:" as const;

export const TAXON_COLLECTION = "com.etzhayyim.apps.seibutsu.taxon";
export const TRAITS_COLLECTION = "com.etzhayyim.apps.seibutsu.traits";
export const OBSERVATION_COLLECTION = "com.etzhayyim.apps.seibutsu.observation";

// ─── Enums ──────────────────────────────────────────────────────────

export type TaxonRank =
  | "domain"
  | "kingdom"
  | "phylum"
  | "class"
  | "order"
  | "family"
  | "genus"
  | "species"
  | "subspecies"
  | "other";

export type Habit = "tree" | "shrub" | "herb" | "grass" | "vine" | "fungus" | "other";

export const TAXON_RANKS: ReadonlySet<string> = new Set([
  "domain",
  "kingdom",
  "phylum",
  "class",
  "order",
  "family",
  "genus",
  "species",
  "subspecies",
  "other",
]);
export const HABITS: ReadonlySet<string> = new Set(["tree", "shrub", "herb", "grass", "vine", "fungus", "other"]);

// ─── Taxon ──────────────────────────────────────────────────────────

export interface TaxonRecord {
  did: string;
  taxonId: string;
  rank: TaxonRank;
  scientificName: string;
  commonName?: string;
  /** Self-ref FK → parent taxon (the hasParent edge). */
  parentTaxonId?: string;
  /** External cross-refs. */
  gbifId?: string;
  ncbiId?: string;
  wikidataId?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface TaxonView extends TaxonRecord {
  taxonUri: string;
}
export interface RegisterTaxonInput {
  taxonId: string;
  rank: TaxonRank;
  scientificName: string;
  commonName?: string;
  parentTaxonId?: string;
  gbifId?: string;
  ncbiId?: string;
  wikidataId?: string;
  sourceUrl?: string;
}
export interface RegisterTaxonOutput {
  status: "registered" | "alreadyExists" | "rejected" | "parentNotFound";
  taxonUri?: string;
  did?: string;
  taxonId?: string;
  error?: string;
}
export interface GetTaxonInput {
  taxonId: string;
}
export interface GetTaxonOutput {
  taxon?: TaxonView;
  error?: string;
}
export interface ListTaxaInput {
  rank?: TaxonRank;
  parentTaxonId?: string;
  /** App-layer substring search over scientific + common name. */
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListTaxaOutput {
  items: TaxonView[];
  cursor?: string;
  total: number;
}

// ─── Traits (procedural profile) ────────────────────────────────────

export interface TraitsRecord {
  did: string;
  traitId: string;
  /** FK → taxon. */
  taxonId: string;
  habit: Habit;
  /** Mature height, cm (integer). */
  matureHeightCm?: number;
  /** Typical lifespan, years (integer). */
  lifespanYears?: number;
  /** USDA-style hardiness zone label, optional. */
  hardinessZone?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface TraitsView extends TraitsRecord {
  traitsUri: string;
}
export interface DeriveTraitsInput {
  traitId: string;
  taxonId: string;
  habit: Habit;
  matureHeightCm?: number;
  lifespanYears?: number;
  hardinessZone?: string;
  sourceUrl?: string;
}
export interface DeriveTraitsOutput {
  status: "derived" | "alreadyExists" | "rejected" | "taxonNotFound";
  traitsUri?: string;
  did?: string;
  traitId?: string;
  error?: string;
}
export interface ListTraitsInput {
  taxonId?: string;
  habit?: Habit;
  limit?: number;
  cursor?: string;
}
export interface ListTraitsOutput {
  items: TraitsView[];
  cursor?: string;
  total: number;
}

// ─── Observation (sighting) ─────────────────────────────────────────

export interface ObservationRecord {
  did: string;
  observationId: string;
  /** FK → taxon. */
  taxonId: string;
  observedAt: string;
  /** Coarsened H3 cell (NOT precise GPS). */
  geoH3?: string;
  /** Public contributor-handle attribution (iNaturalist-style), not raw PII. */
  observerHandle?: string;
  imageUrl?: string;
  sourceUrl?: string;
  createdAt: string;
}
export interface ObservationView extends ObservationRecord {
  observationUri: string;
}
export interface IngestObservationInput {
  observationId: string;
  taxonId: string;
  observedAt: string;
  geoH3?: string;
  observerHandle?: string;
  imageUrl?: string;
  sourceUrl?: string;
}
export interface IngestObservationOutput {
  status: "ingested" | "alreadyExists" | "rejected" | "taxonNotFound";
  observationUri?: string;
  did?: string;
  observationId?: string;
  error?: string;
}
export interface ListObservationsInput {
  taxonId?: string;
  geoH3?: string;
  observerHandle?: string;
  limit?: number;
  cursor?: string;
}
export interface ListObservationsOutput {
  items: ObservationView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  taxonCount?: number;
  traitsCount?: number;
  observationCount?: number;
  taxaByRank?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
/** H3 cell: 15-hex lowercase index (loose check — non-empty hex). */
export function isH3Cell(s: string): boolean {
  return /^[0-9a-f]{8,16}$/.test(s);
}

export function taxonDidFor(id: string): string {
  return `${SEIBUTSU_DID_PREFIX}taxon:${id.toLowerCase()}`;
}
export function taxonRkey(id: string): string {
  return `taxon-${id.toLowerCase()}`;
}
export function traitsDidFor(id: string): string {
  return `${SEIBUTSU_DID_PREFIX}traits:${id.toLowerCase()}`;
}
export function traitsRkey(id: string): string {
  return `traits-${id.toLowerCase()}`;
}
export function observationDidFor(id: string): string {
  return `${SEIBUTSU_DID_PREFIX}obs:${id.toLowerCase()}`;
}
export function observationRkey(id: string): string {
  return `obs-${id.toLowerCase()}`;
}
