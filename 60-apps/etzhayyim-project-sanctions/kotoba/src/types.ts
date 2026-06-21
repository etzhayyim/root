/**
 * sanctions kotoba — public consolidated sanctions-LIST reference record types.
 *
 * Per ADR-2606011400 (Consensys pattern) + ADR-2605172400 (3-axis OR-test).
 *
 * SPLIT (this app is (c) mixed):
 *   PUBLIC list reference (THIS PACKAGE) — the consolidated published sanctions
 *   lists themselves (OFAC SDN/CONS + EU consolidated + UN Security Council +
 *   JP-MOF + UK-OFSI + AU-DFAT + CA-OSFI) plus the per-list refresh/version
 *   tracking. These are authoritative-source OPEN-DATA: the lists are published
 *   by governments and carry NO custody/settlement/fulfillment liability.
 *     → migrated to etzhayyim front (AT PDS records, replaces RW).
 *
 *   SCREENING (STAYS etzhayyim, NOT in this package) — `screenEntity` + the
 *   `sanction_match` audit collection match a CALLER-SUPPLIED subject (customer /
 *   counterparty PII) against the lists and emit an OCEL AML audit event. That
 *   carries screened-subject PII custody (Custody axis) and AML / 善管注意義務
 *   compliance liability (Liability axis), so it remains an etzhayyim regulated
 *   function consumed via consent-capability. Never migrate it.
 *
 * AT-Lexicon: no float. changeCount is an integer. Aliases / identifiers are
 * the PUBLIC sanctioned-entity's own published aliases & doc-ids (passport / IMO
 * / tax-id as printed on the list) — list data, not third-party PII.
 *
 * Identity hierarchy:
 *   did:web:sanctions.etzhayyim.com                          — controller
 *   did:web:sanctions.etzhayyim.com:upd:{updateId}           — a list-refresh snapshot
 *   did:web:sanctions.etzhayyim.com:entry:{entryId}          — a list entry
 */

export const SANCTIONS_DID_PREFIX = "did:web:sanctions.etzhayyim.com:" as const;

export const LIST_UPDATE_COLLECTION = "com.etzhayyim.apps.sanctions.listUpdate";
export const SANCTION_ENTRY_COLLECTION = "com.etzhayyim.apps.sanctions.sanctionEntry";

// ─── List sources + entity types ────────────────────────────────────

export type ListSource =
  | "OFAC-SDN"
  | "OFAC-CONS"
  | "EU"
  | "UN"
  | "JP-MOF"
  | "UK-OFSI"
  | "AU-DFAT"
  | "CA-OSFI"
  | "other";

export type EntityType = "individual" | "entity" | "vessel" | "aircraft" | "other";

export const LIST_SOURCES: ReadonlySet<string> = new Set([
  "OFAC-SDN",
  "OFAC-CONS",
  "EU",
  "UN",
  "JP-MOF",
  "UK-OFSI",
  "AU-DFAT",
  "CA-OSFI",
  "other",
]);
export const ENTITY_TYPES: ReadonlySet<string> = new Set(["individual", "entity", "vessel", "aircraft", "other"]);

// ─── List update (refresh snapshot) ─────────────────────────────────

export interface ListUpdateRecord {
  did: string;
  updateId: string;
  listSource: ListSource;
  listVersion: string;
  /** Number of entries changed in this refresh (integer ≥ 0). */
  changeCount: number;
  fetchedAt: string;
  sourceUrl: string;
  createdAt: string;
}
export interface ListUpdateView extends ListUpdateRecord {
  updateUri: string;
}
export interface RegisterListUpdateInput {
  updateId: string;
  listSource: ListSource;
  listVersion: string;
  changeCount: number;
  fetchedAt: string;
  sourceUrl: string;
}
export interface RegisterListUpdateOutput {
  status: "registered" | "alreadyExists" | "rejected";
  updateUri?: string;
  did?: string;
  updateId?: string;
  error?: string;
}
export interface ListListUpdatesInput {
  listSource?: ListSource;
  limit?: number;
  cursor?: string;
}
export interface ListListUpdatesOutput {
  items: ListUpdateView[];
  cursor?: string;
  total: number;
}

// ─── Sanction entry (list row) ──────────────────────────────────────

export interface SanctionEntryRecord {
  did: string;
  entryId: string;
  listSource: ListSource;
  entityName: string;
  entityType: EntityType;
  /** ISO 3166-1 alpha-2, optional. */
  country?: string;
  program?: string;
  /** Published aliases for the listed entity. */
  aliases?: string[];
  /** Published doc-ids (passport / IMO / tax-id as printed on the list). */
  identifiers?: string[];
  listedDate?: string;
  /** FK → the list-refresh snapshot this entry came in (optional). */
  updateId?: string;
  sourceUrl: string;
  createdAt: string;
}
export interface SanctionEntryView extends SanctionEntryRecord {
  entryUri: string;
}
export interface AddEntryInput {
  entryId: string;
  listSource: ListSource;
  entityName: string;
  entityType: EntityType;
  sourceUrl: string;
  country?: string;
  program?: string;
  aliases?: string[];
  identifiers?: string[];
  listedDate?: string;
  updateId?: string;
}
export interface AddEntryOutput {
  status: "added" | "alreadyExists" | "rejected" | "listUpdateNotFound";
  entryUri?: string;
  did?: string;
  entryId?: string;
  error?: string;
}
export interface GetEntryInput {
  entryId: string;
}
export interface GetEntryOutput {
  entry?: SanctionEntryView;
  error?: string;
}
export interface ListEntriesInput {
  listSource?: ListSource;
  entityType?: EntityType;
  country?: string;
  program?: string;
  /** App-layer substring search over entityName + aliases. */
  q?: string;
  limit?: number;
  cursor?: string;
}
export interface ListEntriesOutput {
  items: SanctionEntryView[];
  cursor?: string;
  total: number;
}

// ─── Coverage ───────────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  entryCount?: number;
  listUpdateCount?: number;
  entriesByListSource?: Record<string, number>;
  entriesByType?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isCountryCode(s: string): boolean {
  return /^[A-Z]{2}$/.test(s);
}
export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}

export function updateDidFor(id: string): string {
  return `${SANCTIONS_DID_PREFIX}upd:${id.toLowerCase()}`;
}
export function updateRkey(id: string): string {
  return `upd-${id.toLowerCase()}`;
}
export function entryDidFor(id: string): string {
  return `${SANCTIONS_DID_PREFIX}entry:${id.toLowerCase()}`;
}
export function entryRkey(id: string): string {
  return `entry-${id.toLowerCase()}`;
}
