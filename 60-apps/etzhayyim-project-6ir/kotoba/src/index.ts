/**
 * 6ir kotoba — barrel.
 *
 * Per ADR-2606011400. Investor-relations intelligence (public open-data) on the
 * etzhayyim substrate (AT PDS records; no RW).
 *
 *   company  : defineCompany / getCompany / listCompanies (q = app-layer search)
 *   filing   : addFiling (FK→company) / getFiling / listFilings
 *   earnings : recordEarnings (FK→company) / listEarnings
 *   analysis : submitAnalysis (FK→company) / listAnalyses
 *   coverage
 *
 * Monetary values are decimal-string micros (AT-Lexicon no float). EPS signed.
 */

export * from "./types.js";
export {
  defineCompany,
  getCompany,
  listCompanies,
  addFiling,
  getFiling,
  listFilings,
  recordEarnings,
  listEarnings,
  submitAnalysis,
  listAnalyses,
  coverage,
} from "./registry.js";
