/**
 * koke rw-free — barrel.
 *
 * Per ADR-2605203000 Option B Phase E reference impl. koke = 苔 (moss),
 * primary fixation in the bonsai biology metaphor. Captures raw external
 * signals (CO₂) and fixes them into structured vertices (glucose),
 * handing off to hakkou (ferment) → ki (absorb/synthesize/bloom).
 *
 * Slice 1: 4 of 4 canonical lexicons ported.
 *   fixSignal + getFixation + listFixations + releaseCarbon
 */

export * from "./types.js";
export {
  fixSignal,
  getFixation,
  listFixations,
  releaseCarbon,
} from "./fixation.js";
