/**
 * sbom rw-free — patch tier (slice 3, +3 → 10/N).
 *
 *   registerPatchPolicy — SLA + auto-decide rules per severity (rkey=patchpolicy-{policyId})
 *   registerPatchAction — concrete patch proposal (rkey=patchaction-{actionId})
 *   getBlastRadius      — composite read: cveId → all affected artifacts + apps
 *
 * The patch SLA from sbom CLAUDE.md:
 *   Critical (≥9.0)  → 24h
 *   High     (≥7.0)  → 72h
 *   Medium   (≥4.0)  → 168h
 *   Low      (<4.0)  → 720h
 *
 * These defaults live in DEFAULT_SLA_HOURS — callers can override per
 * policy via SLA hours field.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  SBOM_DID_PREFIX,
  type BlastRadiusOutput,
  type GetBlastRadiusInput,
  type PatchActionRecord,
  type PatchPolicyRecord,
  type RegisterPatchActionInput,
  type RegisterPatchActionOutput,
  type RegisterPatchPolicyInput,
  type RegisterPatchPolicyOutput,
  type VulnMatchRecord,
} from "./types.js";

const PATCH_POLICY_COLLECTION = "com.etzhayyim.apps.sbom.patchPolicy";
const PATCH_ACTION_COLLECTION = "com.etzhayyim.apps.sbom.patchAction";
const VULN_MATCH_COLLECTION = "com.etzhayyim.apps.sbom.vulnMatch";

/** Default SLA windows (from sbom CLAUDE.md). */
export const DEFAULT_SLA_HOURS = {
  critical: 24,
  high: 72,
  medium: 168,
  low: 720,
  none: 0,
} as const;

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

function patchPolicyRkey(policyId: string): string {
  return `patchpolicy-${policyId.toLowerCase().replace(/[^a-z0-9]/g, "-")}`;
}

function patchPolicyDid(policyId: string): string {
  return `${SBOM_DID_PREFIX}patchpolicy:${policyId.toLowerCase().replace(/[^a-z0-9]/g, "-")}`;
}

function patchActionRkey(actionId: string): string {
  return `patchaction-${actionId.toLowerCase().replace(/[^a-z0-9]/g, "-")}`;
}

function patchActionDid(actionId: string): string {
  return `${SBOM_DID_PREFIX}patchaction:${actionId.toLowerCase().replace(/[^a-z0-9]/g, "-")}`;
}

export async function registerPatchPolicy(
  e: Etzhayyim,
  input: RegisterPatchPolicyInput
): Promise<RegisterPatchPolicyOutput> {
  if (!input.policyId || !input.name) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = patchPolicyRkey(input.policyId);
  const existing = await e
    .read<PatchPolicyRecord>({ collection: PATCH_POLICY_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      patchPolicyUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      policyId: input.policyId,
    };
  }
  const did = patchPolicyDid(input.policyId);
  const record: PatchPolicyRecord = {
    did,
    policyId: input.policyId,
    name: input.name,
    appDid: input.appDid,
    slaHoursCritical: input.slaHoursCritical ?? DEFAULT_SLA_HOURS.critical,
    slaHoursHigh: input.slaHoursHigh ?? DEFAULT_SLA_HOURS.high,
    slaHoursMedium: input.slaHoursMedium ?? DEFAULT_SLA_HOURS.medium,
    slaHoursLow: input.slaHoursLow ?? DEFAULT_SLA_HOURS.low,
    autoDecide: input.autoDecide ?? false,
    notes: input.notes,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: PATCH_POLICY_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "registered",
    patchPolicyUri: receipt.uri,
    did,
    policyId: input.policyId,
  };
}

export async function registerPatchAction(
  e: Etzhayyim,
  input: RegisterPatchActionInput
): Promise<RegisterPatchActionOutput> {
  if (!input.actionId || !input.vulnMatchDid || !input.proposedVersion) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = patchActionRkey(input.actionId);
  const existing = await e
    .read<PatchActionRecord>({ collection: PATCH_ACTION_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      patchActionUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      actionId: input.actionId,
    };
  }
  const did = patchActionDid(input.actionId);
  const record: PatchActionRecord = {
    did,
    actionId: input.actionId,
    vulnMatchDid: input.vulnMatchDid,
    policyDid: input.policyDid,
    proposedVersion: input.proposedVersion,
    decision: input.decision ?? "proposed",
    decisionAt: input.decisionAt,
    decisionBy: input.decisionBy,
    appliedAt: input.appliedAt,
    rolloutPercent: input.rolloutPercent,
    notes: input.notes,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: PATCH_ACTION_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "registered",
    patchActionUri: receipt.uri,
    did,
    actionId: input.actionId,
  };
}

export async function getBlastRadius(
  e: Etzhayyim,
  input: GetBlastRadiusInput
): Promise<BlastRadiusOutput> {
  if (!input.cveId) return { error: "missingCveId" };
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  let cursor: string | undefined;
  let scanned = 0;
  const matches: VulnMatchRecord[] = [];
  while (scanned < maxScan) {
    const page = await e.read<VulnMatchRecord>({
      collection: VULN_MATCH_COLLECTION,
      cursor,
      limit: PAGE_LIMIT,
    });
    for (const r of page.records) {
      if (r.value.cveId === input.cveId) matches.push(r.value);
    }
    scanned += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  const affectedArtifactDids = Array.from(
    new Set(matches.map((m) => m.artifactDid).filter((d): d is string => !!d))
  );
  const affectedAppDids = Array.from(
    new Set(
      matches.map((m) => m.affectedAppDid).filter((d): d is string => !!d)
    )
  );
  const affectedPurls = Array.from(new Set(matches.map((m) => m.componentPurl)));
  return {
    cveId: input.cveId,
    matchCount: matches.length,
    affectedArtifactDids,
    affectedAppDids,
    affectedPurls,
    truncated: scanned >= maxScan,
  };
}
