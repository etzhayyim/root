/**
 * gov rw-free — barrel.
 *
 * Per ADR-2606011400 (Consensys pattern) MIXED split. The public government
 * reference layer on the etzhayyim substrate (AT PDS records; no RW).
 *
 *   agency       : registerAgency (optional parent FK) / getAgency / listAgencies (q = app-layer search)
 *   official     : recordOfficial (FK→agency, public-disclosure) / listOfficials
 *   municipality : registerMunicipality / listMunicipalities
 *   coverage
 *
 * Citizen consultations (submitConsult — potential healthcare/welfare PII) stay
 * etzhayyim infra (consent-capability); not modelled here.
 */

export * from "./types.js";
export {
  registerAgency,
  getAgency,
  listAgencies,
  recordOfficial,
  listOfficials,
  registerMunicipality,
  listMunicipalities,
  coverage,
} from "./registry.js";
