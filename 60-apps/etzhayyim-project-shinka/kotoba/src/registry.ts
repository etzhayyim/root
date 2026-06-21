/**
 * shinka kotoba — registry.
 *
 * Plaintext path (historicalEvent): sdk.write / sdk.read — public historical
 * propagation catalog (the open metadata behind listSponsorable /
 * listPartitions).
 * E2E path (jouchoAssessment): sdk.encryptedWrite / sdk.encryptedRead — per-actor
 * 情緒 5-axis scores + mood + kyumei summary sealed in the kotoba envelope
 * (ADR-2605181100), read-cap = owner DID. The substrate never sees an actor's
 * affective profile in plaintext.
 *
 * FK: recordJoucho rejects unless input.partition exists in the historicalEvent
 * catalog (exists() membership check).
 *
 * Murakumo inference, credit settlement, and postAs social-post EXECUTION stay
 * etzhayyim (consumed via consent-capability); only the resulting data records live
 * here.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  EVENT_COLLECTION,
  JOUCHO_INNER_TYPE,
  eventDidFor,
  eventRkey,
  jouchoRkey,
  isScore,
  isUint,
  type CoverageInput,
  type CoverageOutput,
  type GetJouchoInput,
  type GetJouchoOutput,
  type HistoricalEventRecord,
  type HistoricalEventView,
  type JouchoAssessmentBody,
  type JouchoAssessmentView,
  type ListEventsInput,
  type ListEventsOutput,
  type ListJouchoInput,
  type ListJouchoOutput,
  type RecordJouchoInput,
  type RecordJouchoOutput,
  type SeedEventInput,
  type SeedEventOutput,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Historical event (PLAINTEXT) ───────────────────────────────────

export async function seedEvent(e: Etzhayyim, input: SeedEventInput): Promise<SeedEventOutput> {
  if (!input.eventId || !input.title || !input.partition || !input.eventAt) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  if (!isUint(input.propagationCount)) return { status: "rejected", error: "invalidPropagationCount" };
  const rkey = eventRkey(input.eventId);
  const existing = await e
    .read<HistoricalEventRecord>({ collection: EVENT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      eventUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      eventId: input.eventId,
    };
  }
  const now = new Date().toISOString();
  const did = eventDidFor(input.eventId);
  const record: HistoricalEventRecord = {
    did,
    eventId: input.eventId,
    title: input.title,
    partition: input.partition,
    eventAt: input.eventAt,
    propagationCount: input.propagationCount,
    sponsorable: input.sponsorable ?? false,
    createdAt: now,
  };
  const receipt = await e.write({ collection: EVENT_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "recorded", eventUri: receipt.uri, did, eventId: input.eventId };
}

export async function listEvents(e: Etzhayyim, input: ListEventsInput = {}): Promise<ListEventsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<HistoricalEventRecord>({ collection: EVENT_COLLECTION, cursor: input.cursor, limit });
  const items: HistoricalEventView[] = resp.records
    .filter((r) => !input.partition || r.value.partition === input.partition)
    .filter((r) => !input.sponsorableOnly || r.value.sponsorable)
    .map((r) => ({ ...r.value, eventUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

/** FK helper: does a historicalEvent with the given partition exist? */
async function partitionExists(e: Etzhayyim, partition: string, maxScan = DEFAULT_MAX_SCAN): Promise<boolean> {
  let cursor: string | undefined;
  let scanned = 0;
  while (scanned < maxScan) {
    const page = await e.read<HistoricalEventRecord>({ collection: EVENT_COLLECTION, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      scanned += 1;
      if (r.value.partition === partition) return true;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  return false;
}

// ─── Joucho assessment (E2E-ENCRYPTED, per-actor CUI) ───────────────

export async function recordJoucho(e: Etzhayyim, input: RecordJouchoInput): Promise<RecordJouchoOutput> {
  if (!input.assessmentId || !input.actorDid || !input.partition || !input.mood) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  for (const v of [input.joy, input.calm, input.stress, input.gratitude, input.focus]) {
    if (!isScore(v)) return { status: "rejected", error: "invalidScore" };
  }
  // FK: partition must reference a known historicalEvent partition.
  if (!(await partitionExists(e, input.partition))) {
    return { status: "rejected", error: "unknownPartition" };
  }
  const body: JouchoAssessmentBody = {
    assessmentId: input.assessmentId,
    actorDid: input.actorDid,
    partition: input.partition,
    joy: input.joy,
    calm: input.calm,
    stress: input.stress,
    gratitude: input.gratitude,
    focus: input.focus,
    mood: input.mood,
    summary: input.summary,
    assessedAt: input.assessedAt ?? new Date().toISOString(),
  };
  // Read-cap = owner DID (sender, auto-wrapped) + any explicit recipients.
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: JOUCHO_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: jouchoRkey(input.assessmentId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, assessmentId: input.assessmentId };
}

async function scanJoucho(e: Etzhayyim, maxScan: number): Promise<JouchoAssessmentView[]> {
  const out: JouchoAssessmentView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<JouchoAssessmentBody>({ innerType: JOUCHO_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    }
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listJoucho(e: Etzhayyim, input: ListJouchoInput = {}): Promise<ListJouchoOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanJoucho(e, DEFAULT_MAX_SCAN);
  const filtered = all
    .filter((j) => !input.partition || j.partition === input.partition)
    .filter((j) => !input.mood || j.mood === input.mood);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getJoucho(e: Etzhayyim, input: GetJouchoInput): Promise<GetJouchoOutput> {
  if (!input.assessmentId) return { error: "invalidAssessmentId" };
  const all = await scanJoucho(e, DEFAULT_MAX_SCAN);
  const found = all.find((j) => j.assessmentId === input.assessmentId);
  if (!found) return { error: "notFound" };
  return { assessment: found };
}

// ─── Coverage rollup ────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const eventsByPartition: Record<string, number> = {};
  let historicalEventCount = 0;
  let cursor: string | undefined;
  while (historicalEventCount < maxScan) {
    const page = await e.read<HistoricalEventRecord>({ collection: EVENT_COLLECTION, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      eventsByPartition[r.value.partition] = (eventsByPartition[r.value.partition] ?? 0) + 1;
      historicalEventCount += 1;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }
  const jouchoAssessmentCount = (await scanJoucho(e, maxScan)).length;
  return {
    historicalEventCount,
    jouchoAssessmentCount,
    eventsByPartition,
    truncated: historicalEventCount >= maxScan || jouchoAssessmentCount >= maxScan,
  };
}
