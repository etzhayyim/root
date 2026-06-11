/**
 * business-person rw-free — barrel.
 *
 * Per ADR-2606011400. Public registry of corporate officers / executives / board
 * members on the etzhayyim substrate (AT PDS records; no RW).
 *
 *   person      : registerPerson / getPerson / listPersons (q = app-layer search)
 *   appointment : addAppointment (FK→person) / endAppointment / listAppointments
 *   coverage
 *
 * Tier-1 public-disclosure data only; private PII (Tier-3) stays in natural-person.
 */

export * from "./types.js";
export {
  registerPerson,
  getPerson,
  listPersons,
  addAppointment,
  endAppointment,
  listAppointments,
  coverage,
} from "./registry.js";
