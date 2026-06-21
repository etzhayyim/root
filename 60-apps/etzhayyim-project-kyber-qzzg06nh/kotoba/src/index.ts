/**
 * kyber-qzzg06nh kotoba — barrel.
 *
 * Per ADR-2606011400 + ADR-0025. The kyber-qzzg06nh knowledge-graph on the
 * etzhayyim substrate (AT PDS records; no RW).
 *
 *   entity : defineEntity / getEntity / listEntities (q = app-layer search) / archiveEntity
 *   event  : recordEvent (FK→entity) / listEvents
 *   report : submitReport (optional FK→entity) / publishReport / listReports
 *   coverage
 */

export * from "./types.js";
export {
  defineEntity,
  getEntity,
  listEntities,
  archiveEntity,
  recordEvent,
  listEvents,
  submitReport,
  publishReport,
  listReports,
  coverage,
} from "./registry.js";
