/**
 * otakiage kotoba — barrel.
 *
 * Per ADR-2605081700 + ADR-2605203000 Option B Phase E reference impl.
 * otakiage = reuse + ritual platform — single state machine per item.
 *
 * Slice 1: 3 of 10 lexicons ported.
 *   submitItem + getItem + listItems
 *
 * Follow-up slices:
 * - State transitions: requestReuse, handover, expire, requestRitual, ritualize
 * - Certificate: anchorCertificate, issueCertificate
 * - Matsuri: scheduleMatsuri
 * - Reports: coverage
 * - LLM: agentChat (LangServer pod-side)
 */

export * from "./types.js";
export { submitItem, getItem, listItems } from "./itemRegistry.js";
export {
  requestReuse,
  handover,
  expire,
  requestRitual,
  ritualize,
} from "./transitions.js";
export {
  issueCertificate,
  anchorCertificate,
  scheduleMatsuri,
  coverage,
  agentChat,
} from "./final.js";
