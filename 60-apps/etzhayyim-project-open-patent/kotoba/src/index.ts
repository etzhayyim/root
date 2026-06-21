/**
 * open-patent kotoba — barrel.
 *
 * Per ADR-2606011400. Public patent open-data + open IP generation on the
 * etzhayyim substrate (AT PDS records; no RW).
 *
 *   patent   : ingestPatent / getPatent / listPatents (q = app-layer search)
 *   citation : addCitation (FK→patent) / listCitations
 *   seed     : synthesizeSeed / publishSeed / listSeeds (open invention IP)
 *   novelty  : addNoveltyReport (FK→seed, per-mille score) / listNoveltyReports
 *   coverage
 *
 * Public/open data; invention seeds published as open prior-art.
 */

export * from "./types.js";
export {
  ingestPatent,
  getPatent,
  listPatents,
  addCitation,
  listCitations,
  synthesizeSeed,
  publishSeed,
  listSeeds,
  addNoveltyReport,
  listNoveltyReports,
  coverage,
} from "./registry.js";
