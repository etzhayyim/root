/**
 * hc kotoba — barrel. Intel E2E reference pattern (plaintext public-meta +
 * kotoba-E2E sensitive payload, ADR-2605181100).
 *
 * Plaintext: contract templates (public legal catalog).
 * E2E: SP KYC/KYB applications (PII + CUI sealed via sdk.encryptedWrite/Read).
 * Stays etzhayyim: fiat shift settlement, USDC escrow, sanctions-screening execution,
 * credential custody — consumed via consent-capability.
 */
export * from "./types.js";
export {
  registerContract,
  getContract,
  listContracts,
  registerSpApplication,
  listSpApplications,
  getSpApplication,
  coverage,
} from "./registry.js";
