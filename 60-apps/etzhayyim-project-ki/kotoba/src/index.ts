/**
 * ki kotoba — barrel.
 *
 * Per ADR-2605203000 Option B Phase E reference implementation.
 * Per kiyo project bonsai biology metaphor: ki = 樹液 (sap) — vascular
 * system carrying signals from absorb (xylem) through synthesize
 * (photosynthesis) to bloom (phloem) with ring (dendrochronology)
 * snapshots.
 *
 * Slice 1: 4 of 4 canonical lexicons ported.
 *   absorb + synthesize + bloom + ring
 *
 * Architectural note: vendor's ki is a thin-edge dispatcher proxying
 * to dispatcher.etzhayyim.com. On the etzhayyim substrate, the LangServer pod
 * owns the LLM call (synthesize stage) and writes the SynthesisRecord
 * via e.write() — the CF Worker is a pure thin XRPC facade. This
 * package supplies the persistence layer used by both pod and Worker.
 */

export * from "./types.js";
export { absorb, synthesize, bloom, ring, mapRoute, getStatus } from "./vascular.js";
