/**
 * sbom rw-free — barrel.
 *
 * Per ADR-2605203000 Option B Phase E reference implementation.
 * NOT a Worker — pure TS module to be wired into an XRPC handler.
 *
 * Slice 1: 4 of N commands ported.
 *   registerArtifact + getArtifact   — SbomArtifact tier
 *   registerComponent + listComponents — SbomComponent tier
 *
 * Follow-up slices: VulnMatch / PatchPolicy / PatchAction tiers + CVE
 * blast-radius pipeline (cveIngestOsv / runVulnMatch / getBlastRadius /
 * createPatchAction).
 */

export * from "./types.js";
export {
  registerArtifact,
  getArtifact,
  registerComponent,
  listComponents,
} from "./artifactRegistry.js";
export {
  cveIngestOsv,
  registerVulnMatch,
  listVulnMatches,
} from "./vulnRegistry.js";
export {
  registerPatchPolicy,
  registerPatchAction,
  getBlastRadius,
  DEFAULT_SLA_HOURS,
} from "./patchRegistry.js";
export {
  getSlaTimer,
  listOverdueVulnMatches,
  getArtifactDependents,
  analyzeApp,
} from "./analyze.js";
export { recall, updateComponentSupplier, health } from "./recall.js";
