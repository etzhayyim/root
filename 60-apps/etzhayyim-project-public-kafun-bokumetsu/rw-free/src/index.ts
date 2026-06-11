/**
 * public-kafun-bokumetsu rw-free — barrel.
 *
 * Per ADR-2606011400. The pollen-eradication research/action/capability layer on
 * the etzhayyim substrate (AT PDS records; no RW).
 *
 *   research   : recordResearch / getResearch / concludeResearch / listResearch (q = app-layer search)
 *   capability : defineCapability / listCapabilities
 *   action     : proposeAction (optional FK→research, capability refs) / setActionStatus / listActions
 *   coverage
 *
 * Public environmental/health research data; no PII / settlement / liability.
 */

export * from "./types.js";
export {
  recordResearch,
  getResearch,
  concludeResearch,
  listResearch,
  defineCapability,
  listCapabilities,
  proposeAction,
  setActionStatus,
  listActions,
  coverage,
} from "./registry.js";
