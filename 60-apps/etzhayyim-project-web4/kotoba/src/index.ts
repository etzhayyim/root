/**
 * web4 kotoba — barrel. kotoba-E2E split for the browser-MoE compute
 * marketplace: public model/expert/market catalog plaintext; provider PII +
 * commercial terms, private inference jobs, and Compute Credit ledger movements
 * E2E (sdk.encryptedWrite/Read, ADR-2605181100). GPU/LLM inference execution,
 * fiat on-ramp settlement for CC purchases, and the 100B-scale S3 expert-weight
 * archive stay etzhayyim via consent-capability.
 */
export * from "./types.js";
export {
  registerModelManifest,
  listModelManifests,
  registerExpert,
  getExpert,
  listExperts,
  recordMarketStat,
  listMarketStats,
  registerProvider,
  listProviders,
  getProvider,
  submitInference,
  listJobs,
  getJob,
  postLedgerEntry,
  listLedger,
  accountBalance,
  coverage,
} from "./registry.js";
