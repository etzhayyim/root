/**
 * open-kyber rw-free — barrel. Open-source ERP (APQC-aligned), kotoba-E2E split
 * (ADR-2605181100): public accounting reference + integration catalog plaintext,
 * Tier-3 HR PII (employee) sealed via kotoba E2E. Fiat merchant-of-record usage
 * metering + warehouse/edge persistence EXECUTION stay etzhayyim via consent-capability.
 */
export * from "./types.js";
export {
  createAccount,
  listAccounts,
  registerIntegration,
  listIntegrations,
  registerEmployee,
  listEmployees,
  getEmployee,
  coverage,
} from "./registry.js";
