/**
 * saiban kotoba — barrel.
 *
 * Per ADR-2606011400 (Consensys pattern) MIXED split. The public judicial-
 * reference layer on the etzhayyim substrate (AT PDS records; no RW).
 *
 *   court           : registerCourt (optional parent FK) / getCourt / listCourts (q = app-layer search)
 *   judge           : addJudge (FK→court, public official) / listJudges
 *   jurisdictionMap : mapJurisdiction (FK→court) / listJurisdictionMaps
 *   coverage
 *
 * jiken (case) + trialEvent (party PII / confidential litigation) stay etzhayyim / E2E.
 */

export * from "./types.js";
export {
  registerCourt,
  getCourt,
  listCourts,
  addJudge,
  listJudges,
  mapJurisdiction,
  listJurisdictionMaps,
  coverage,
} from "./registry.js";
