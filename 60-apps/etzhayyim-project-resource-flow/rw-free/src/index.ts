/**
 * resource-flow rw-free — barrel.
 *
 * Per ADR-2606011400. Public 2次ソース resource-flow visualization data on the
 * etzhayyim substrate (AT PDS records; no RW).
 *
 *   emitter : registerEmitter / listEmitters (registered flow sources)
 *   flow    : recordFlow (FK→emitter, decimal-string amount) / listFlows
 *   anomaly : recordAnomaly (FK→emitter) / reviewAnomaly (ACK/DIS/ESC) / listAnomalies
 *   coverage
 *
 * (c) MIXED SPLIT: the public flow/emitter/anomaly DATA migrates (externally-
 * authored by gov + legal-entity emitters). The anomaly-detection algorithm
 * (BPMN R/PT24H) + sankey-MV aggregation are derived COMPUTE that stays etzhayyim,
 * consumed via consent-capability — NOT in this package.
 */

export * from "./types.js";
export {
  registerEmitter,
  listEmitters,
  recordFlow,
  listFlows,
  recordAnomaly,
  reviewAnomaly,
  listAnomalies,
  coverage,
} from "./registry.js";
