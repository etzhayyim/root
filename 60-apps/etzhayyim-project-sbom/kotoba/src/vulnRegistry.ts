/**
 * sbom kotoba — vulnerability tier (slice 2, +3 → 7/N).
 *
 *   cveIngestOsv      — ingest one OSV/CVE entry (idempotent rkey=cve-{id})
 *   registerVulnMatch — record a (cveId × component-purl) match
 *                       (idempotent rkey=vulnmatch-{cveId}-{purl-slug})
 *   listVulnMatches   — cursor + cveId/purl/severity filter
 *
 * Pipeline:
 *   ct-monitor → cveIngestOsv (poll OSV feed) → CveEntry
 *   sbom run-vuln-match → CveEntry × Component → registerVulnMatch
 *   getBlastRadius(cveId) → all affected artifacts/apps
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  purlSlug,
  SBOM_DID_PREFIX,
  type CveEntryRecord,
  type CveEntryView,
  type CveIngestOsvInput,
  type CveIngestOsvOutput,
  type ListVulnMatchesInput,
  type ListVulnMatchesOutput,
  type RegisterVulnMatchInput,
  type RegisterVulnMatchOutput,
  type VulnMatchRecord,
  type VulnMatchView,
  type ComponentRecord,
} from "./types.js";
import { componentRegistry } from "./artifactRegistry.js";

const CVE_COLLECTION = "com.etzhayyim.apps.sbom.cve";
const VULN_MATCH_COLLECTION = "com.etzhayyim.apps.sbom.vulnMatch";
const COMPONENT_COLLECTION = "com.etzhayyim.apps.sbom.component";

function cveSlug(cveId: string): string {
  return cveId.toLowerCase().replace(/[^a-z0-9]/g, "-");
}

function cveDid(cveId: string): string {
  return `${SBOM_DID_PREFIX}cve:${cveSlug(cveId)}`;
}

function cveRkey(cveId: string): string {
  return `cve-${cveSlug(cveId)}`;
}

function vulnMatchSlug(cveId: string, purl: string): string {
  return `${cveSlug(cveId)}-${purlSlug(purl)}`;
}

function vulnMatchDid(cveId: string, purl: string): string {
  return `${SBOM_DID_PREFIX}vulnmatch:${vulnMatchSlug(cveId, purl)}`;
}

function vulnMatchRkey(cveId: string, purl: string): string {
  return `vulnmatch-${vulnMatchSlug(cveId, purl)}`;
}

export async function cveIngestOsv(
  e: Etzhayyim,
  input: CveIngestOsvInput
): Promise<CveIngestOsvOutput> {
  if (!input.cveId || !input.osvPayload) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = cveRkey(input.cveId);
  const existing = await e
    .read<CveEntryRecord>({ collection: CVE_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      cveUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      cveId: input.cveId,
    };
  }
  const did = cveDid(input.cveId);
  const p = input.osvPayload;
  const record: CveEntryRecord = {
    did,
    cveId: input.cveId,
    summary: p.summary,
    details: p.details,
    severity: p.severity,
    /** CVSS × 10 (no float) — e.g. 9.8 → 98. */
    cvssPermille: p.cvssPermille,
    publishedAt: p.publishedAt,
    modifiedAt: p.modifiedAt,
    affectedEcosystems: p.affectedEcosystems,
    affectedPurlPrefixes: p.affectedPurlPrefixes,
    references: p.references,
    aliases: p.aliases,
    sourceUrl: input.sourceUrl,
    osvSchemaVersion: input.osvSchemaVersion,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: CVE_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "created",
    cveUri: receipt.uri,
    did,
    cveId: input.cveId,
  };
}

export async function registerVulnMatch(
  e: Etzhayyim,
  input: RegisterVulnMatchInput
): Promise<RegisterVulnMatchOutput> {
  // Normalize inputs from alternate field names
  const cveId = input.cveId ?? input.cvId;
  let componentPurl = input.componentPurl ?? input.componentId;

  if (!cveId || !componentPurl) {
    return { status: "rejected", error: "missingRequiredFields" };
  }

  // If componentId was provided, look it up in the registry to get the purl
  const componentId = input.componentId;
  if (componentId && componentRegistry.has(componentId)) {
    const comp = componentRegistry.get(componentId)!;
    componentPurl = comp.purl;
  } else if (componentId && !componentRegistry.has(componentId)) {
    // componentId provided but not found
    return { status: "rejected", error: "vulnMatchNotFound" };
  }

  const rkey = vulnMatchRkey(cveId, componentPurl);
  const existing = await e
    .read<VulnMatchRecord>({ collection: VULN_MATCH_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      vulnMatchUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      cveId,
      componentPurl,
    };
  }
  const did = vulnMatchDid(cveId, componentPurl);
  const record: VulnMatchRecord = {
    did,
    cveId,
    componentPurl,
    artifactDid: input.artifactDid,
    affectedAppDid: input.affectedAppDid,
    matchConfidencePermille: input.matchConfidencePermille,
    severity: input.severity,
    cvssPermille: input.cvssPermille,
    fixedVersion: input.fixedVersion,
    status: input.status ?? "open",
    discoveredAt: new Date().toISOString(),
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: VULN_MATCH_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "created",
    vulnMatchUri: receipt.uri,
    did,
    cveId,
    componentPurl,
  };
}

export async function listVulnMatches(
  e: Etzhayyim,
  input: ListVulnMatchesInput = {}
): Promise<ListVulnMatchesOutput> {
  const limit = Math.min(input.limit ?? 50, 100);
  const resp = await e.read<VulnMatchRecord>({
    collection: VULN_MATCH_COLLECTION,
    cursor: input.cursor,
    limit,
  });
  const items: VulnMatchView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.cveId && v.cveId !== input.cveId) return false;
      if (input.componentPurl && v.componentPurl !== input.componentPurl) {
        return false;
      }
      if (input.artifactDid && v.artifactDid !== input.artifactDid) {
        return false;
      }
      if (input.affectedAppDid && v.affectedAppDid !== input.affectedAppDid) {
        return false;
      }
      if (input.severity && v.severity !== input.severity) return false;
      if (input.status && v.status !== input.status) return false;
      return true;
    })
    .map((r) => ({ ...r.value, vulnMatchUri: r.uri }));
  const filteredItems = items.length > 0 ? items : [];
  return { items: filteredItems, cursor: resp.cursor, total: filteredItems.length };
}

/** Re-export of view type for analyze tier. */
export type { CveEntryView };
