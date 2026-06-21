/**
 * sbom kotoba — analyze + SLA tier (slice 4, +4 → 14/N).
 *
 *   getSlaTimer           — SLA deadline + remaining time for one VulnMatch
 *                           (severity × policy.slaHours from discoveredAt)
 *   listOverdueVulnMatches — paged listing of VulnMatches past their SLA
 *   getArtifactDependents — components depending (transitively) on a given purl
 *   analyzeApp            — composite report for one app:
 *                           open VulnMatches + overdue counts by severity
 *
 * Phase 3 mst-projector adds indexed time-window views to push the
 * SLA scan server-side at O(1); current impl scans VulnMatch up to
 * maxScan with honest truncated:boolean response.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import { DEFAULT_SLA_HOURS } from "./patchRegistry.js";
import {
  type AnalyzeAppInput,
  type AnalyzeAppOutput,
  type ComponentRecord,
  type GetArtifactDependentsInput,
  type GetArtifactDependentsOutput,
  type GetSlaTimerInput,
  type GetSlaTimerOutput,
  type ListOverdueVulnMatchesInput,
  type ListOverdueVulnMatchesOutput,
  type PatchPolicyRecord,
  type Purl,
  type VulnMatchRecord,
  type VulnMatchView,
  type VulnSeverity,
} from "./types.js";

const COMPONENT_COLLECTION = "com.etzhayyim.apps.sbom.component";
const VULN_MATCH_COLLECTION = "com.etzhayyim.apps.sbom.vulnMatch";
const PATCH_POLICY_COLLECTION = "com.etzhayyim.apps.sbom.patchPolicy";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

function severityToHours(
  severity: VulnSeverity | undefined,
  policy: PatchPolicyRecord | undefined
): number {
  if (!severity || severity === "none") {
    return policy?.slaHoursLow ?? DEFAULT_SLA_HOURS.low;
  }
  if (severity === "critical") {
    return policy?.slaHoursCritical ?? DEFAULT_SLA_HOURS.critical;
  }
  if (severity === "high") {
    return policy?.slaHoursHigh ?? DEFAULT_SLA_HOURS.high;
  }
  if (severity === "medium") {
    return policy?.slaHoursMedium ?? DEFAULT_SLA_HOURS.medium;
  }
  return policy?.slaHoursLow ?? DEFAULT_SLA_HOURS.low;
}

function slaDeadline(
  discoveredAt: string,
  hours: number
): string {
  const t = new Date(discoveredAt).getTime() + hours * 3_600_000;
  return new Date(t).toISOString();
}

function patchPolicyRkeyFromDid(did: string): string {
  const slug = did.split(":").pop() ?? did;
  return `patchpolicy-${slug.toLowerCase().replace(/[^a-z0-9]/g, "-")}`;
}

export async function getSlaTimer(
  e: Etzhayyim,
  input: GetSlaTimerInput
): Promise<GetSlaTimerOutput> {
  if (!input.vulnMatchDid) return { error: "missingVulnMatchDid" };
  // Read VulnMatch by scanning — no rkey-direct path since the rkey
  // requires both cveId + purl. A Phase 3 indexed view solves this;
  // for now we look it up by did.
  const limit = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  let cursor: string | undefined;
  let scanned = 0;
  let match: VulnMatchRecord | undefined;
  while (scanned < limit && !match) {
    const page = await e.read<VulnMatchRecord>({
      collection: VULN_MATCH_COLLECTION,
      cursor,
      limit: PAGE_LIMIT,
    });
    match = page.records.find((r) => r.value.did === input.vulnMatchDid)
      ?.value;
    scanned += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  if (!match) return { error: "vulnMatchNotFound" };

  let policy: PatchPolicyRecord | undefined;
  if (input.policyDid) {
    const pr = await e
      .read<PatchPolicyRecord>({
        collection: PATCH_POLICY_COLLECTION,
        rkey: patchPolicyRkeyFromDid(input.policyDid),
      })
      .catch(() => ({ records: [] }));
    policy = pr.records[0]?.value;
  }

  const hours = severityToHours(match.severity, policy);
  const deadlineAt = slaDeadline(match.discoveredAt, hours);
  const now = Date.now();
  const remainingMs = new Date(deadlineAt).getTime() - now;
  return {
    vulnMatchDid: match.did,
    severity: match.severity,
    slaHours: hours,
    discoveredAt: match.discoveredAt,
    deadlineAt,
    remainingMs,
    overdue: remainingMs < 0,
  };
}

export async function listOverdueVulnMatches(
  e: Etzhayyim,
  input: ListOverdueVulnMatchesInput = {}
): Promise<ListOverdueVulnMatchesOutput> {
  const limit = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const now = Date.now();
  let cursor: string | undefined;
  let scanned = 0;
  const overdue: VulnMatchView[] = [];
  while (scanned < limit) {
    const page = await e.read<VulnMatchRecord>({
      collection: VULN_MATCH_COLLECTION,
      cursor,
      limit: PAGE_LIMIT,
    });
    for (const r of page.records) {
      const v = r.value;
      if (v.status === "patched" || v.status === "wontfix" || v.status === "false-positive") {
        continue;
      }
      if (input.affectedAppDid && v.affectedAppDid !== input.affectedAppDid) {
        continue;
      }
      const hours = severityToHours(v.severity, undefined);
      const deadlineMs = new Date(v.discoveredAt).getTime() + hours * 3_600_000;
      if (deadlineMs < now) {
        overdue.push({ ...v, vulnMatchUri: r.uri });
      }
    }
    scanned += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return {
    items: overdue,
    total: overdue.length,
    truncated: scanned >= limit,
  };
}

export async function getArtifactDependents(
  e: Etzhayyim,
  input: GetArtifactDependentsInput
): Promise<GetArtifactDependentsOutput> {
  if (!input.purl) return { error: "missingPurl" };
  const limit = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  let cursor: string | undefined;
  let scanned = 0;
  const directDependents: Purl[] = [];
  const allComponents = new Map<Purl, ComponentRecord>();
  while (scanned < limit) {
    const page = await e.read<ComponentRecord>({
      collection: COMPONENT_COLLECTION,
      cursor,
      limit: PAGE_LIMIT,
    });
    for (const r of page.records) {
      allComponents.set(r.value.purl, r.value);
      if (r.value.dependsOn?.includes(input.purl)) {
        directDependents.push(r.value.purl);
      }
    }
    scanned += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  // Transitive close.
  const visited = new Set<Purl>([input.purl, ...directDependents]);
  const queue = [...directDependents];
  while (queue.length > 0) {
    const cur = queue.shift()!;
    for (const c of allComponents.values()) {
      if (c.dependsOn?.includes(cur) && !visited.has(c.purl)) {
        visited.add(c.purl);
        queue.push(c.purl);
      }
    }
  }
  visited.delete(input.purl);
  return {
    purl: input.purl,
    directDependents,
    transitiveDependents: [...visited],
    truncated: scanned >= limit,
  };
}

export async function analyzeApp(
  e: Etzhayyim,
  input: AnalyzeAppInput
): Promise<AnalyzeAppOutput> {
  if (!input.appDid) return { error: "missingAppDid" };
  const limit = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const now = Date.now();
  let cursor: string | undefined;
  let scanned = 0;
  let openTotal = 0;
  const overdueBy: Record<VulnSeverity, number> = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    none: 0,
  };
  const openBy: Record<VulnSeverity, number> = {
    critical: 0,
    high: 0,
    medium: 0,
    low: 0,
    none: 0,
  };
  while (scanned < limit) {
    const page = await e.read<VulnMatchRecord>({
      collection: VULN_MATCH_COLLECTION,
      cursor,
      limit: PAGE_LIMIT,
    });
    for (const r of page.records) {
      const v = r.value;
      if (v.affectedAppDid !== input.appDid) continue;
      if (
        v.status === "patched" ||
        v.status === "wontfix" ||
        v.status === "false-positive"
      ) {
        continue;
      }
      openTotal += 1;
      const sev = v.severity ?? "none";
      openBy[sev] += 1;
      const hours = severityToHours(v.severity, undefined);
      const deadlineMs =
        new Date(v.discoveredAt).getTime() + hours * 3_600_000;
      if (deadlineMs < now) overdueBy[sev] += 1;
    }
    scanned += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return {
    appDid: input.appDid,
    openTotal,
    openBy,
    overdueBy,
    truncated: scanned >= limit,
  };
}
