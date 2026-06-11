/**
 * crypto-asset-freeze rw-free — barrel. kotoba-E2E split: plaintext public
 * aggregate (incidentProjection) + E2E CUI/LE bodies (freezeIncident,
 * freezeRequest), ADR-2605181100. Freeze/unfreeze execution + recursive
 * wallet-trace inference stay etzhayyim (consent-capability).
 */
export * from "./types.js";
export {
  recordProjection,
  listProjections,
  createIncident,
  listIncidents,
  getIncident,
  requestFreeze,
  listRequests,
  coverage,
} from "./registry.js";
