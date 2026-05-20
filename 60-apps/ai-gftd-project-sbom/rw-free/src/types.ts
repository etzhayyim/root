/**
 * sbom rw-free — record types.
 *
 * Per ADR-2605203000 Option B (PDS XRPC). SBOM = Software Bill of Materials.
 * gftd build → SBOM auto-gen → yabai CVE match → blast radius → completer.
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

export interface ArtifactRecord {
  did: string;
  /** Content-addressed identifier — full SHA-256 of the SBOM file. */
  sha256: string;
  format: SbomFormat;
  /** App / project the SBOM was built FOR (Yata App reference). */
  builtForAppDid?: string;
  builtAt?: string;
  generator?: string;
  /** Total component count parsed from the SBOM. */
  componentCount?: number;
  sourceUrl?: string;
  createdAt: string;
}

export interface ArtifactView extends ArtifactRecord {
  artifactUri: string;
}

export interface RegisterArtifactInput {
  sha256: string;
  format: SbomFormat;
  builtForAppDid?: string;
  builtAt?: string;
  generator?: string;
  componentCount?: number;
  sourceUrl?: string;
}

export interface RegisterArtifactOutput {
  status: "registered" | "alreadyExists" | "rejected";
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
  version?: string;
  ecosystem?: string;
  license?: string[];
  /** Parent artifact this component belongs to. */
  artifactDid?: string;
  /** Direct dependency parent purls (graph relationship). */
  dependsOn?: Purl[];
  createdAt: string;
}

export interface ComponentView extends ComponentRecord {
  componentUri: string;
}

export interface RegisterComponentInput {
  purl: Purl;
  name: string;
  version?: string;
  ecosystem?: string;
  license?: string[];
  artifactDid?: string;
  dependsOn?: Purl[];
}

export interface RegisterComponentOutput {
  status: "registered" | "alreadyExists" | "rejected";
  componentUri?: string;
  did?: string;
  purl?: Purl;
  error?: string;
}

export interface ListComponentsInput {
  artifactDid?: string;
  ecosystem?: string;
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
  status: "registered" | "alreadyExists" | "rejected";
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
  cveId: string;
  componentPurl: Purl;
  artifactDid?: string;
  affectedAppDid?: string;
  matchConfidencePermille?: number;
  severity?: VulnSeverity;
  cvssPermille?: number;
  fixedVersion?: string;
  status?: VulnMatchStatus;
}

export interface RegisterVulnMatchOutput {
  status: "registered" | "alreadyExists" | "rejected";
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
