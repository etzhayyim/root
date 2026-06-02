/**
 * open-cofog rw-free — barrel.
 *
 * Per ADR-2605203000 Option B. UN COFOG government-function taxonomy on the
 * etzhayyim substrate (AT PDS records; no RW).
 *
 *   registry : registerEntry / getEntry / listEntries / coverage
 *   helpers  : cofogLevel / parentOf / ancestorsOf / isValidCofogCode
 */

export * from "./types.js";
export {
  registerEntry,
  getEntry,
  listEntries,
  coverage,
} from "./registry.js";
