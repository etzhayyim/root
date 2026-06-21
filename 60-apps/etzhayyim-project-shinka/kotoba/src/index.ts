/**
 * shinka kotoba — barrel. Actor Shinka evolution scheduler under the kotoba-E2E
 * split (plaintext historical-propagation catalog + per-actor 情緒 joucho
 * assessment sealed via kotoba E2E, ADR-2605181100). Murakumo inference, credit
 * settlement, and postAs social-post execution stay etzhayyim via consent-capability.
 */
export * from "./types.js";
export {
  seedEvent,
  listEvents,
  recordJoucho,
  listJoucho,
  getJoucho,
  coverage,
} from "./registry.js";
