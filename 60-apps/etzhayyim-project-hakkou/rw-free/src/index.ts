/**
 * hakkou rw-free — barrel.
 *
 * Per ADR-2605203000 Option B Phase E reference impl. hakkou = 発酵 —
 * irreversible fermentation transforming koke fixations (glucose) into
 * structured knowledge (ethanol) for ki absorb tier.
 *
 * Slice 1: 2 of 2 canonical lexicons ported + 1 helper.
 *   startFerment + getFerment + updateFermentStatus (helper)
 */

export * from "./types.js";
export {
  startFerment,
  getFerment,
  updateFermentStatus as updateFermentStatusForFerment,
} from "./ferment.js";
export {
  registerBatch,
  getBatch,
  listBatches,
  updateFermentStatus,
} from "./batches.js";
