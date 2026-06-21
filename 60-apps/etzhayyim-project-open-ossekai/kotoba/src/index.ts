/**
 * open-ossekai kotoba — barrel. kotoba-E2E split (plaintext L2 public-good
 * arbitrage catalog + kotoba-E2E L3 consent-gated jocho PII, ADR-2605181100 +
 * ADR-0018). L1 LLM intel-brief / scoring inference + fiat sales-lead
 * propagation stay etzhayyim via consent-capability.
 */
export * from "./types.js";
export {
  registerArbitrage,
  getArbitrage,
  listArbitrage,
  recordJocho,
  listJocho,
  getJocho,
  coverage,
} from "./registry.js";
