/**
 * public-kafun-bokumetsu rw-free — research + action + capability registries +
 * coverage. AT PDS records (no RW). Actions optionally FK→research and carry
 * mapped capability refs. Public pollen-eradication research data only.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ACTION_COLLECTION,
  ACTION_STATUSES,
  CAPABILITY_COLLECTION,
  CATEGORIES,
  RESEARCH_COLLECTION,
  actionDidFor,
  actionRkey,
  capabilityDidFor,
  capabilityRkey,
  researchDidFor,
  researchRkey,
  type ActionRecord,
  type ActionView,
  type CapabilityRecord,
  type CapabilityView,
  type ConcludeResearchInput,
  type ConcludeResearchOutput,
  type CoverageInput,
  type CoverageOutput,
  type DefineCapabilityInput,
  type DefineCapabilityOutput,
  type GetResearchInput,
  type GetResearchOutput,
  type ListActionsInput,
  type ListActionsOutput,
  type ListCapabilitiesInput,
  type ListCapabilitiesOutput,
  type ListResearchInput,
  type ListResearchOutput,
  type ProposeActionInput,
  type ProposeActionOutput,
  type RecordResearchInput,
  type RecordResearchOutput,
  type ResearchRecord,
  type ResearchView,
  type SetActionStatusInput,
  type SetActionStatusOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

async function exists(e: Etzhayyim, collection: string, rkey: string): Promise<boolean> {
  const resp = await e.read({ collection, rkey }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

async function scanAll<T>(e: Etzhayyim, collection: string, maxScan: number, onRow: (v: T) => void): Promise<number> {
  let cursor: string | undefined;
  let scanned = 0;
  while (scanned < maxScan) {
    const page = await e.read<T>({ collection, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      if (scanned >= maxScan) break;
      onRow(r.value);
      scanned += 1;
    }
    if (scanned >= maxScan || !page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return scanned;
}

// ─── Research ───────────────────────────────────────────────────────

export async function recordResearch(e: Etzhayyim, input: RecordResearchInput): Promise<RecordResearchOutput> {
  if (!input.researchId || !input.title) return { status: "rejected", error: "missingRequiredFields" };
  if (!CATEGORIES.has(input.category)) return { status: "rejected", error: "invalidCategory" };
  const rkey = researchRkey(input.researchId);
  const existing = await e.read<ResearchRecord>({ collection: RESEARCH_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", researchUri: existing.records[0].uri, did: existing.records[0].value.did, researchId: input.researchId };
  }
  const did = researchDidFor(input.researchId);
  const record: ResearchRecord = {
    did,
    researchId: input.researchId,
    category: input.category,
    title: input.title,
    summary: input.summary,
    status: "open",
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: RESEARCH_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", researchUri: receipt.uri, did, researchId: input.researchId };
}

export async function getResearch(e: Etzhayyim, input: GetResearchInput): Promise<GetResearchOutput> {
  if (!input.researchId) return { error: "invalidResearchId" };
  const resp = await e.read<ResearchRecord>({ collection: RESEARCH_COLLECTION, rkey: researchRkey(input.researchId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  return { research: { ...r.value, researchUri: r.uri } };
}

export async function concludeResearch(e: Etzhayyim, input: ConcludeResearchInput): Promise<ConcludeResearchOutput> {
  if (!input.researchId) return { status: "rejected", error: "invalidResearchId" };
  const rkey = researchRkey(input.researchId);
  const resp = await e.read<ResearchRecord>({ collection: RESEARCH_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const research = resp.records[0]?.value;
  if (!research) return { status: "notFound", error: "researchNotFound" };
  if (research.status === "concluded") return { status: "rejected", error: "alreadyConcluded" };
  await e.write({ collection: RESEARCH_COLLECTION, record: { ...research, status: "concluded" } as unknown as Record<string, unknown>, rkey });
  return { status: "concluded", researchId: input.researchId };
}

export async function listResearch(e: Etzhayyim, input: ListResearchInput = {}): Promise<ListResearchOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ResearchRecord>({ collection: RESEARCH_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: ResearchView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.category && v.category !== input.category) return false;
      if (input.status && v.status !== input.status) return false;
      if (q && !v.title.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, researchUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Capability ─────────────────────────────────────────────────────

export async function defineCapability(e: Etzhayyim, input: DefineCapabilityInput): Promise<DefineCapabilityOutput> {
  if (!input.capabilityId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  const rkey = capabilityRkey(input.capabilityId);
  const existing = await e.read<CapabilityRecord>({ collection: CAPABILITY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", capabilityUri: existing.records[0].uri, did: existing.records[0].value.did, capabilityId: input.capabilityId };
  }
  const did = capabilityDidFor(input.capabilityId);
  const record: CapabilityRecord = {
    did,
    capabilityId: input.capabilityId,
    name: input.name,
    description: input.description,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: CAPABILITY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "defined", capabilityUri: receipt.uri, did, capabilityId: input.capabilityId };
}

export async function listCapabilities(e: Etzhayyim, input: ListCapabilitiesInput = {}): Promise<ListCapabilitiesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<CapabilityRecord>({ collection: CAPABILITY_COLLECTION, cursor: input.cursor, limit });
  const items: CapabilityView[] = resp.records.map((r) => ({ ...r.value, capabilityUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Action ─────────────────────────────────────────────────────────

export async function proposeAction(e: Etzhayyim, input: ProposeActionInput): Promise<ProposeActionOutput> {
  if (!input.actionId || !input.title) return { status: "rejected", error: "missingRequiredFields" };
  if (input.researchId && !(await exists(e, RESEARCH_COLLECTION, researchRkey(input.researchId)))) {
    return { status: "researchNotFound", error: `researchNotFound:${input.researchId}` };
  }
  const rkey = actionRkey(input.actionId);
  const existing = await e.read<ActionRecord>({ collection: ACTION_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", actionUri: existing.records[0].uri, did: existing.records[0].value.did, actionId: input.actionId };
  }
  const did = actionDidFor(input.actionId);
  const record: ActionRecord = {
    did,
    actionId: input.actionId,
    title: input.title,
    description: input.description,
    researchId: input.researchId,
    capabilityRefs: (input.capabilityRefs ?? []).map((s) => s.toLowerCase()),
    status: "proposed",
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: ACTION_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "proposed", actionUri: receipt.uri, did, actionId: input.actionId };
}

export async function setActionStatus(e: Etzhayyim, input: SetActionStatusInput): Promise<SetActionStatusOutput> {
  if (!input.actionId || !ACTION_STATUSES.has(input.status)) return { status: "rejected", error: "invalidStatus" };
  const rkey = actionRkey(input.actionId);
  const resp = await e.read<ActionRecord>({ collection: ACTION_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const action = resp.records[0]?.value;
  if (!action) return { status: "notFound", error: "actionNotFound" };
  if (action.status === "done" || action.status === "cancelled") {
    return { status: "rejected", error: `actionTerminal:${action.status}` };
  }
  await e.write({ collection: ACTION_COLLECTION, record: { ...action, status: input.status } as unknown as Record<string, unknown>, rkey });
  return { status: "updated", actionId: input.actionId, newStatus: input.status };
}

export async function listActions(e: Etzhayyim, input: ListActionsInput = {}): Promise<ListActionsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<ActionRecord>({ collection: ACTION_COLLECTION, cursor: input.cursor, limit });
  const capRef = input.capabilityRef?.toLowerCase();
  const items: ActionView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.researchId && v.researchId !== input.researchId) return false;
      if (input.status && v.status !== input.status) return false;
      if (capRef && !v.capabilityRefs.includes(capRef)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, actionUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const researchByCategory: Record<string, number> = {};
  const researchCount = await scanAll<ResearchRecord>(e, RESEARCH_COLLECTION, maxScan, (v) => {
    researchByCategory[v.category] = (researchByCategory[v.category] ?? 0) + 1;
  });
  const actionsByStatus: Record<string, number> = {};
  const actionCount = await scanAll<ActionRecord>(e, ACTION_COLLECTION, maxScan, (v) => {
    actionsByStatus[v.status] = (actionsByStatus[v.status] ?? 0) + 1;
  });
  const capabilityCount = await scanAll<CapabilityRecord>(e, CAPABILITY_COLLECTION, maxScan, () => {});
  return {
    researchCount,
    actionCount,
    capabilityCount,
    researchByCategory,
    actionsByStatus,
    truncated: researchCount >= maxScan || actionCount >= maxScan || capabilityCount >= maxScan,
  };
}
