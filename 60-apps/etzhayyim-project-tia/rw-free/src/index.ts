/**
 * tia rw-free — barrel. Internet Account Protection front with kotoba-E2E split
 * (public platform catalog plaintext + account PII / detection findings sealed
 * via kotoba E2E, ADR-2605181100). Gemini similarity inference + platform
 * takedown actions stay etzhayyim via consent-capability.
 */
export * from "./types.js";
export {
  registerPlatform,
  getPlatform,
  listPlatforms,
  registerAccount,
  listAccounts,
  getAccount,
  recordDetection,
  listDetections,
  coverage,
} from "./registry.js";
