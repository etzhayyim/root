/**
 * sbom rw-free — record types.
 *
 * Per ADR-2605203000 Option B (PDS XRPC). SBOM = Software Bill of Materials.
 * etzhayyim build → SBOM auto-gen → yabai CVE match → blast radius → completer.
 *
 * Identity hierarchy (per sbom CLAUDE.md graph relationships):
 *   did:web:sbom.etzhayyim.com                              — controller
 *   did:web:sbom.etzhayyim.com:artifact:{sha256-short}       — SbomArtifact
 *   did:web:sbom.etzhayyim.com:component:{purl-slug}         — SbomComponent
 *   did:web:sbom.etzhayyim.com:vulnmatch:{cve-id}-{purl-slug} — VulnMatch
 *   did:web:sbom.etzhayyim.com:patchpolicy:{policy-id}       — PatchPolicy
 *   did:web:sbom.etzhayyim.com:patchaction:{action-id}       — PatchAction
 *
 * Slice 1 of N: artifact + component tier (4 commands).
 */

export const SBOM_DID_PREFIX = "did:web:sbom.etzhayyim.com:" as const;

export type SbomFormat = "cyclonedx-1.5" | "spdx-3.0";

// ─── Artifact tier (slice 1) ────────────────────────────────────────

export type SbomKind = "software" | "vehicle";

export interface ArtifactRecord {
  did: string;
  /** Content-addressed identifier — full SHA-256 of the SBOM file. */
  sha256: string;
  /** Semantic identifier / name (e.g. "app-1.0"). */
  artifactId?: string;
  format: SbomFormat;
  /** App / project the SBOM was built FOR (Yata App reference). */
  builtForAppDid?: string;
  builtAt?: string;
  generator?: string;
  /** Total component count parsed from the SBOM. */
  componentCount?: number;
  /** software (default for app SBOMs) | vehicle (hardware BOM). */
  kind?: SbomKind;
  sourceUrl?: string;
  createdAt: string;
}

export interface ArtifactView extends ArtifactRecord {
  artifactUri: string;
}

export interface RegisterArtifactInput {
  sha256: string;
  artifactId?: string;
  artifactType?: string;
  name?: string;
  format?: SbomFormat;
  builtForAppDid?: string;
  builtAt?: string;
  generator?: string;
  componentCount?: number;
  sourceUrl?: string;
}

export interface RegisterArtifactOutput {
  status: "registered" | "created" | "alreadyExists" | "rejected";
  artifactUri?: string;
  did?: string;
  sha256?: string;
  error?: string;
}

export interface GetArtifactInput {
  sha256?: string;
}

export interface GetArtifactOutput {
  artifact?: ArtifactView;
  error?: string;
}

// ─── Component tier (slice 1) ───────────────────────────────────────

/**
 * Package URL (purl) — RFC-compatible component identifier.
 * e.g. pkg:npm/lodash@4.17.21, pkg:cargo/serde@1.0
 */
export type Purl = string;

export interface ComponentRecord {
  did: string;
  purl: Purl;
  name: string;
  componentType?: string;
  version?: string;
  ecosystem?: string;
  license?: string[];
  /** Parent artifact this component belongs to. */
  artifactDid?: string;
  /** Direct dependency parent purls (graph relationship). */
  dependsOn?: Purl[];
  /** Supplier (vendor / manufacturer) — populated by updateComponentSupplier. */
  supplierName?: string;
  supplierMpn?: string;
  supplierCountry?: string;
  supplierUpdatedAt?: string;
  createdAt: string;
}

export interface ComponentView extends ComponentRecord {
  componentUri: string;
}

export interface RegisterComponentInput {
  purl?: Purl;
  componentId?: string;
  artifactId?: string;
  artifactDid?: string;
  name: string;
  componentType?: string;
  version?: string;
  ecosystem?: string;
  license?: string[];
  dependsOn?: Purl[];
}

export interface RegisterComponentOutput {
  status: "registered" | "created" | "alreadyExists" | "rejected";
  componentUri?: string;
  did?: string;
  purl?: Purl;
  error?: string;
}

export interface ListComponentsInput {
  artifactId?: string;
  artifactDid?: string;
  ecosystem?: string;
  componentType?: string;
  limit?: number;
  cursor?: string;
}

export interface ListComponentsOutput {
  items: ComponentView[];
  cursor?: string;
  total: number;
}

// ─── Slug helpers ───────────────────────────────────────────────────

/** Short SHA-256 prefix for DID/rkey (first 12 hex chars). */
export function sha256Short(sha256: string): string {
  return sha256.toLowerCase().slice(0, 12);
}

export function artifactDid(sha256: string): string {
  return `${SBOM_DID_PREFIX}artifact:${sha256Short(sha256)}`;
}

export function artifactRkey(sha256: string): string {
  return `artifact-${sha256Short(sha256)}`;
}

/** purl slug — lowercase + replace non-alphanumeric. */
export function purlSlug(purl: Purl): string {
  return purl.toLowerCase().replace(/[^a-z0-9]/g, "-");
}

export function componentDid(purl: Purl): string {
  return `${SBOM_DID_PREFIX}component:${purlSlug(purl)}`;
}

export function componentRkey(purl: Purl): string {
  return `component-${purlSlug(purl)}`;
}

// ─── CVE / VulnMatch tier (slice 2) ─────────────────────────────────

export type VulnSeverity = "critical" | "high" | "medium" | "low" | "none";
export type VulnMatchStatus =
  | "open"
  | "triaged"
  | "patched"
  | "wontfix"
  | "false-positive";

export interface OsvPayload {
  summary?: string;
  details?: string;
  severity?: VulnSeverity;
  /** CVSS × 10 (no float, 0-100 maps to 0.0-10.0). */
  cvssPermille?: number;
  publishedAt?: string;
  modifiedAt?: string;
  affectedEcosystems?: string[];
  affectedPurlPrefixes?: string[];
  references?: string[];
  aliases?: string[];
}

export interface CveEntryRecord {
  did: string;
  cveId: string;
  summary?: string;
  details?: string;
  severity?: VulnSeverity;
  cvssPermille?: number;
  publishedAt?: string;
  modifiedAt?: string;
  affectedEcosystems?: string[];
  affectedPurlPrefixes?: string[];
  references?: string[];
  aliases?: string[];
  sourceUrl?: string;
  osvSchemaVersion?: string;
  createdAt: string;
}

export interface CveEntryView extends CveEntryRecord {
  cveUri: string;
}

export interface CveIngestOsvInput {
  cveId: string;
  osvPayload: OsvPayload;
  sourceUrl?: string;
  osvSchemaVersion?: string;
}

export interface CveIngestOsvOutput {
  status: "registered" | "created" | "alreadyExists" | "rejected";
  cveUri?: string;
  did?: string;
  cveId?: string;
  error?: string;
}

export interface VulnMatchRecord {
  did: string;
  cveId: string;
  componentPurl: Purl;
  artifactDid?: string;
  affectedAppDid?: string;
  /** 0-1000 (permille — no float per AT Lexicon). */
  matchConfidencePermille?: number;
  severity?: VulnSeverity;
  cvssPermille?: number;
  fixedVersion?: string;
  status: VulnMatchStatus;
  discoveredAt: string;
  createdAt: string;
}

export interface VulnMatchView extends VulnMatchRecord {
  vulnMatchUri: string;
}

export interface RegisterVulnMatchInput {
  cveId?: string;
  cvId?: string;
  vulnMatchId?: string;
  componentPurl?: Purl;
  componentId?: string;
  artifactDid?: string;
  affectedAppDid?: string;
  matchConfidencePermille?: number;
  severity?: VulnSeverity;
  cvssPermille?: number;
  fixedVersion?: string;
  status?: VulnMatchStatus;
}

export interface RegisterVulnMatchOutput {
  status: "registered" | "created" | "alreadyExists" | "rejected";
  vulnMatchUri?: string;
  did?: string;
  cveId?: string;
  componentPurl?: Purl;
  error?: string;
}

export interface ListVulnMatchesInput {
  cveId?: string;
  componentPurl?: Purl;
  artifactDid?: string;
  affectedAppDid?: string;
  severity?: VulnSeverity;
  status?: VulnMatchStatus;
  limit?: number;
  cursor?: string;
}

export interface ListVulnMatchesOutput {
  items: VulnMatchView[];
  cursor?: string;
  total: number;
}

// ─── Patch tier (slice 3) ───────────────────────────────────────────

export interface PatchPolicyRecord {
  did: string;
  policyId: string;
  name: string;
  appDid?: string;
  slaHoursCritical: number;
  slaHoursHigh: number;
  slaHoursMedium: number;
  slaHoursLow: number;
  autoDecide: boolean;
  notes?: string;
  createdAt: string;
}

export interface RegisterPatchPolicyInput {
  policyId: string;
  name: string;
  appDid?: string;
  slaHoursCritical?: number;
  slaHoursHigh?: number;
  slaHoursMedium?: number;
  slaHoursLow?: number;
  autoDecide?: boolean;
  notes?: string;
}

export interface RegisterPatchPolicyOutput {
  status: "registered" | "created" | "alreadyExists" | "rejected";
  patchPolicyUri?: string;
  did?: string;
  policyId?: string;
  error?: string;
}

export type PatchDecision =
  | "proposed"
  | "approved"
  | "rejected"
  | "applied"
  | "rolled-back";

export interface PatchActionRecord {
  did: string;
  actionId: string;
  vulnMatchDid: string;
  policyDid?: string;
  proposedVersion: string;
  decision: PatchDecision;
  decisionAt?: string;
  decisionBy?: string;
  appliedAt?: string;
  /** 0-1000 (permille) — rollout percentage at time of apply. */
  rolloutPercent?: number;
  notes?: string;
  createdAt: string;
}

export interface RegisterPatchActionInput {
  actionId: string;
  vulnMatchDid: string;
  policyDid?: string;
  proposedVersion: string;
  decision?: PatchDecision;
  decisionAt?: string;
  decisionBy?: string;
  appliedAt?: string;
  rolloutPercent?: number;
  notes?: string;
}

export interface RegisterPatchActionOutput {
  status: "registered" | "created" | "alreadyExists" | "rejected";
  patchActionUri?: string;
  did?: string;
  actionId?: string;
  error?: string;
}

export interface GetBlastRadiusInput {
  cveId: string;
  maxScan?: number;
}

export interface BlastRadiusOutput {
  cveId?: string;
  matchCount?: number;
  affectedArtifactDids?: string[];
  affectedAppDids?: string[];
  affectedPurls?: Purl[];
  truncated?: boolean;
  error?: string;
}

// ─── Analyze + SLA tier (slice 4) ───────────────────────────────────

export interface GetSlaTimerInput {
  vulnMatchDid: string;
  policyDid?: string;
  maxScan?: number;
}

export interface GetSlaTimerOutput {
  vulnMatchDid?: string;
  severity?: VulnSeverity;
  slaHours?: number;
  discoveredAt?: string;
  deadlineAt?: string;
  remainingMs?: number;
  overdue?: boolean;
  error?: string;
}

export interface ListOverdueVulnMatchesInput {
  affectedAppDid?: string;
  maxScan?: number;
}

export interface ListOverdueVulnMatchesOutput {
  items?: VulnMatchView[];
  total?: number;
  truncated?: boolean;
  error?: string;
}

export interface GetArtifactDependentsInput {
  purl: Purl;
  maxScan?: number;
}

export interface GetArtifactDependentsOutput {
  purl?: Purl;
  directDependents?: Purl[];
  transitiveDependents?: Purl[];
  truncated?: boolean;
  error?: string;
}

export interface AnalyzeAppInput {
  appDid: string;
  maxScan?: number;
}

export interface AnalyzeAppOutput {
  appDid?: string;
  openTotal?: number;
  openBy?: Record<VulnSeverity, number>;
  overdueBy?: Record<VulnSeverity, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Recall + Health tier (slice 5) ─────────────────────────────────

export interface RecallInput {
  supplier: string;
  mpn?: string;
  kind?: SbomKind;
  limit?: number;
  offset?: number;
  maxScan?: number;
}

export interface RecallMatch {
  artifactUri: string;
  artifactDid: string;
  kind?: SbomKind;
  componentBomRef: Purl;
  supplier: string;
  mpn?: string;
  name?: string;
  version?: string;
}

export interface RecallOutput {
  matches?: RecallMatch[];
  total?: number;
  limit?: number;
  offset?: number;
  truncated?: boolean;
  error?: string;
}

export interface UpdateComponentSupplierInput {
  purl: Purl;
  supplierName: string;
  supplierMpn?: string;
  supplierCountry?: string;
}

export interface UpdateComponentSupplierOutput {
  status: "updated" | "rejected";
  componentUri?: string;
  purl?: Purl;
  error?: string;
}

export interface HealthOutput {
  status: "ok" | "degraded" | "down";
  actor: string;
  substrate: string;
  timestamp: string;
}
