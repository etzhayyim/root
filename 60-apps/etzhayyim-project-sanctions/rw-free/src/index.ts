/**
 * sanctions rw-free — barrel.
 *
 * Per ADR-2606011400 (Consensys pattern). Public consolidated sanctions-LIST
 * reference on the etzhayyim substrate (AT PDS records; no RW).
 *
 *   listUpdate    : registerListUpdate / listListUpdates (per-list refresh tracking)
 *   sanctionEntry : addEntry (FK→listUpdate) / getEntry / listEntries (q = name+alias search)
 *   coverage
 *
 * (c) MIXED SPLIT: the lists are authoritative-source open-data. The
 * `screenEntity` screening function + `sanction_match` audit trail (caller's
 * customer/counterparty PII custody + AML / 善管注意義務 liability) STAY etzhayyim and
 * are consumed via consent-capability — NOT part of this package.
 */

export * from "./types.js";
export {
  registerListUpdate,
  listListUpdates,
  addEntry,
  getEntry,
  listEntries,
  coverage,
} from "./registry.js";
