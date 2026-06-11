/**
 * seibutsu (生物) rw-free — barrel.
 *
 * Per ADR-2606011400. Public biodiversity taxonomy open-data on the etzhayyim
 * substrate (AT PDS records; no RW) — the GBIF / iNaturalist model.
 *
 *   taxon       : registerTaxon (self-ref parent FK) / getTaxon / listTaxa (q = name search)
 *   traits      : deriveTraits (FK→taxon, integer cm/years) / listTraits
 *   observation : ingestObservation (FK→taxon, H3 geo, public observer handle) / listObservations
 *   coverage
 *
 * (a) etzhayyim front. The image→species `identify` capability (Murakumo fleet
 * inference) is AI compute and stays etzhayyim; the catalog itself is open-data.
 */

export * from "./types.js";
export {
  registerTaxon,
  getTaxon,
  listTaxa,
  deriveTraits,
  listTraits,
  ingestObservation,
  listObservations,
  coverage,
} from "./registry.js";
