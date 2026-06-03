/**
 * resource-flow rw-free — emitter + flow + anomaly registries + coverage.
 * AT PDS records (no RW). Flows & anomalies FK→emitter (by source DID). Public
 * 2次ソース data only; anomaly-detection + sankey-MV compute stays etzhayyim.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ANOMALY_COLLECTION,
  EMITTER_COLLECTION,
  FLOW_CLASSES,
  FLOW_COLLECTION,
  REVIEW_STATUSES,
  SEVERITIES,
  SOURCE_TYPES,
  anomalyDidFor,
  anomalyRkey,
  emitterRkey,
  flowDidFor,
  flowRkey,
  isUintString,
  type AnomalyRecord,
  type AnomalyView,
  type CoverageInput,
  type CoverageOutput,
  type EmitterRecord,
  type EmitterView,
  type FlowRecord,
  type FlowView,
  type ListAnomaliesInput,
  type ListAnomaliesOutput,
  type ListEmittersInput,
  type ListEmittersOutput,
  type ListFlowsInput,
  type ListFlowsOutput,
  type RecordAnomalyInput,
  type RecordAnomalyOutput,
  type RecordFlowInput,
  type RecordFlowOutput,
  type RegisterEmitterInput,
  type RegisterEmitterOutput,
  type ReviewAnomalyInput,
  type ReviewAnomalyOutput,
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

// ─── Emitter ────────────────────────────────────────────────────────

export async function registerEmitter(e: Etzhayyim, input: RegisterEmitterInput): Promise<RegisterEmitterOutput> {
  if (!input.emitterDid || !input.label) return { status: "rejected", error: "missingRequiredFields" };
  if (!SOURCE_TYPES.has(input.sourceType)) return { status: "rejected", error: "invalidSourceType" };
  if (input.flowClasses && input.flowClasses.some((c) => !FLOW_CLASSES.has(c))) return { status: "rejected", error: "invalidFlowClass" };
  const rkey = emitterRkey(input.emitterDid);
  const existing = await e.read<EmitterRecord>({ collection: EMITTER_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", emitterUri: existing.records[0].uri, did: existing.records[0].value.did, emitterDid: input.emitterDid };
  }
  const record: EmitterRecord = {
    did: input.emitterDid,
    emitterDid: input.emitterDid,
    label: input.label,
    sourceType: input.sourceType,
    flowClasses: input.flowClasses,
    rootDid: input.rootDid,
    registeredAt: input.registeredAt ?? new Date().toISOString(),
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: EMITTER_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", emitterUri: receipt.uri, did: input.emitterDid, emitterDid: input.emitterDid };
}

export async function listEmitters(e: Etzhayyim, input: ListEmittersInput = {}): Promise<ListEmittersOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<EmitterRecord>({ collection: EMITTER_COLLECTION, cursor: input.cursor, limit });
  const q = input.q?.toLowerCase();
  const items: EmitterView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.sourceType && v.sourceType !== input.sourceType) return false;
      if (q && !v.label.toLowerCase().includes(q)) return false;
      return true;
    })
    .map((r) => ({ ...r.value, emitterUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Flow edge ──────────────────────────────────────────────────────

export async function recordFlow(e: Etzhayyim, input: RecordFlowInput): Promise<RecordFlowOutput> {
  if (!input.flowId || !input.sourceDid || !input.counterpartyDid || !input.amount || !input.observedAt) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!FLOW_CLASSES.has(input.flowClass)) return { status: "rejected", error: "invalidFlowClass" };
  if (!isUintString(input.amount)) return { status: "rejected", error: "amountMustBeUintString" };
  if (!(await exists(e, EMITTER_COLLECTION, emitterRkey(input.sourceDid)))) {
    return { status: "emitterNotFound", error: `emitterNotFound:${input.sourceDid}` };
  }
  const rkey = flowRkey(input.flowId);
  const existing = await e.read<FlowRecord>({ collection: FLOW_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", flowUri: existing.records[0].uri, did: existing.records[0].value.did, flowId: input.flowId };
  }
  const did = flowDidFor(input.flowId);
  const record: FlowRecord = {
    did,
    flowId: input.flowId,
    flowClass: input.flowClass,
    sourceDid: input.sourceDid,
    counterpartyDid: input.counterpartyDid,
    amount: input.amount,
    unit: input.unit,
    period: input.period,
    sourceRootDid: input.sourceRootDid,
    counterpartyRootDid: input.counterpartyRootDid,
    observedAt: input.observedAt,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: FLOW_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", flowUri: receipt.uri, did, flowId: input.flowId };
}

export async function listFlows(e: Etzhayyim, input: ListFlowsInput = {}): Promise<ListFlowsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<FlowRecord>({ collection: FLOW_COLLECTION, cursor: input.cursor, limit });
  const items: FlowView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.flowClass && v.flowClass !== input.flowClass) return false;
      if (input.sourceDid && v.sourceDid !== input.sourceDid) return false;
      if (input.counterpartyDid && v.counterpartyDid !== input.counterpartyDid) return false;
      return true;
    })
    .map((r) => ({ ...r.value, flowUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Anomaly ────────────────────────────────────────────────────────

export async function recordAnomaly(e: Etzhayyim, input: RecordAnomalyInput): Promise<RecordAnomalyOutput> {
  if (!input.anomalyId || !input.sourceDid || !input.description || !input.detectedAt) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!FLOW_CLASSES.has(input.flowClass)) return { status: "rejected", error: "invalidFlowClass" };
  if (!SEVERITIES.has(input.severity)) return { status: "rejected", error: "invalidSeverity" };
  if (input.reviewStatus && !REVIEW_STATUSES.has(input.reviewStatus)) return { status: "rejected", error: "invalidReviewStatus" };
  if (!(await exists(e, EMITTER_COLLECTION, emitterRkey(input.sourceDid)))) {
    return { status: "emitterNotFound", error: `emitterNotFound:${input.sourceDid}` };
  }
  const rkey = anomalyRkey(input.anomalyId);
  const existing = await e.read<AnomalyRecord>({ collection: ANOMALY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", anomalyUri: existing.records[0].uri, did: existing.records[0].value.did, anomalyId: input.anomalyId };
  }
  const did = anomalyDidFor(input.anomalyId);
  const record: AnomalyRecord = {
    did,
    anomalyId: input.anomalyId,
    flowClass: input.flowClass,
    sourceDid: input.sourceDid,
    severity: input.severity,
    description: input.description,
    reviewStatus: input.reviewStatus ?? "open",
    detectedAt: input.detectedAt,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({ collection: ANOMALY_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", anomalyUri: receipt.uri, did, anomalyId: input.anomalyId };
}

export async function reviewAnomaly(e: Etzhayyim, input: ReviewAnomalyInput): Promise<ReviewAnomalyOutput> {
  if (!input.anomalyId || !REVIEW_STATUSES.has(input.reviewStatus)) return { status: "rejected", error: "invalidReviewStatus" };
  const rkey = anomalyRkey(input.anomalyId);
  const resp = await e.read<AnomalyRecord>({ collection: ANOMALY_COLLECTION, rkey }).catch(() => ({ records: [] }));
  const anomaly = resp.records[0]?.value;
  if (!anomaly) return { status: "notFound", error: "anomalyNotFound" };
  await e.write({ collection: ANOMALY_COLLECTION, record: { ...anomaly, reviewStatus: input.reviewStatus } as unknown as Record<string, unknown>, rkey });
  return { status: "updated", anomalyId: input.anomalyId, newStatus: input.reviewStatus };
}

export async function listAnomalies(e: Etzhayyim, input: ListAnomaliesInput = {}): Promise<ListAnomaliesOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<AnomalyRecord>({ collection: ANOMALY_COLLECTION, cursor: input.cursor, limit });
  const items: AnomalyView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.flowClass && v.flowClass !== input.flowClass) return false;
      if (input.sourceDid && v.sourceDid !== input.sourceDid) return false;
      if (input.severity && v.severity !== input.severity) return false;
      if (input.reviewStatus && v.reviewStatus !== input.reviewStatus) return false;
      return true;
    })
    .map((r) => ({ ...r.value, anomalyUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Coverage ───────────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const flowsByClass: Record<string, number> = {};
  const anomaliesBySeverity: Record<string, number> = {};
  const emitterCount = await scanAll<EmitterRecord>(e, EMITTER_COLLECTION, maxScan, () => {});
  const flowCount = await scanAll<FlowRecord>(e, FLOW_COLLECTION, maxScan, (v) => {
    flowsByClass[v.flowClass] = (flowsByClass[v.flowClass] ?? 0) + 1;
  });
  const anomalyCount = await scanAll<AnomalyRecord>(e, ANOMALY_COLLECTION, maxScan, (v) => {
    anomaliesBySeverity[v.severity] = (anomaliesBySeverity[v.severity] ?? 0) + 1;
  });
  return {
    emitterCount,
    flowCount,
    anomalyCount,
    flowsByClass,
    anomaliesBySeverity,
    truncated: emitterCount >= maxScan || flowCount >= maxScan || anomalyCount >= maxScan,
  };
}
