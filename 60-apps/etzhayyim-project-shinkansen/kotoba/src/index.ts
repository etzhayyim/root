/**
 * shinkansen (新幹線) kotoba — barrel.
 *
 * Per ADR-2606011400. Public rail reference (lines + timetables + fares +
 * operation status) on the etzhayyim substrate (AT PDS records; no RW).
 *
 *   line      : registerLine / listLines
 *   timetable : addTimetable (FK→line, HH:MM times) / listTimetable
 *   fare      : addFare (seatClass/fareType/platform enums, JPY string) / listFares (cheapest highlight)
 *   operation : recordOperation (FK→line, status + delayMinutes) / listOperations
 *   coverage
 *
 * (c) MIXED SPLIT: the public catalog migrates. `reserveSeat` +
 * `searchAvailability` + the reservation collection (Tier-3 PII: name/payment/
 * seat) + live SmartEX/ekinet booking proxies (Settlement) STAY etzhayyim and are
 * consumed via consent-capability — NOT part of this package.
 */

export * from "./types.js";
export {
  registerLine,
  listLines,
  addTimetable,
  listTimetable,
  addFare,
  listFares,
  recordOperation,
  listOperations,
  coverage,
} from "./registry.js";
