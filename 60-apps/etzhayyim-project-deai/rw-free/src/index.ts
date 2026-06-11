/**
 * deai rw-free — barrel. Spirit-in-Physics matching, kotoba-E2E split
 * (plaintext spiritTypeCatalog + cohortStat; E2E spiritProfile + matchScore,
 * ADR-2605181100). Hume biometric inference + match-engine execution stay etzhayyim
 * via consent-capability.
 */
export * from "./types.js";
export {
  registerSpiritType,
  getSpiritType,
  listSpiritTypes,
  recordCohortStat,
  listCohortStats,
  recordProfile,
  listProfiles,
  getProfile,
  recordMatch,
  listMatches,
  getMatch,
  coverage,
} from "./registry.js";
