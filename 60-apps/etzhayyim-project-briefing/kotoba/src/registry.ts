/**
 * briefing kotoba registry — kotoba-E2E split.
 *
 * Plaintext path (room / agendaItem): sdk.write / sdk.read — public meeting
 * structure + catalog metadata, no PII.
 * E2E path (transcript / recordingAsset / actionItem / decision):
 * sdk.encryptedWrite / sdk.encryptedRead — meeting content + per-person data
 * sealed in the kotoba envelope (ADR-2605181100), read-cap = owner DID +
 * explicit recipients. The substrate never sees spoken words / ballots /
 * assignee identities in plaintext.
 *
 * STAYS etzhayyim via consent-capability: the raw R2/B2 recording-blob archive and
 * the GPU/LLM inference acts (STT / translate / summarize / extract).
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  ACTION_ITEM_INNER_TYPE,
  AGENDA_COLLECTION,
  DECISION_INNER_TYPE,
  RECORDING_INNER_TYPE,
  ROOM_COLLECTION,
  TRANSCRIPT_INNER_TYPE,
  actionItemRkey,
  agendaRkey,
  decisionRkey,
  isPct,
  isUint,
  recordingRkey,
  roomDidFor,
  roomRkey,
  transcriptRkey,
  type ActionItemBody,
  type ActionItemView,
  type AgendaItemRecord,
  type AgendaItemView,
  type CoverageInput,
  type CoverageOutput,
  type DecisionBody,
  type DecisionView,
  type GetDecisionInput,
  type GetDecisionOutput,
  type GetRoomInput,
  type GetRoomOutput,
  type GetTranscriptInput,
  type GetTranscriptOutput,
  type ListActionItemsInput,
  type ListActionItemsOutput,
  type ListAgendaInput,
  type ListAgendaOutput,
  type ListDecisionsInput,
  type ListDecisionsOutput,
  type ListRecordingsInput,
  type ListRecordingsOutput,
  type ListRoomsInput,
  type ListRoomsOutput,
  type ListTranscriptsInput,
  type ListTranscriptsOutput,
  type RecordActionItemInput,
  type RecordActionItemOutput,
  type RecordDecisionInput,
  type RecordDecisionOutput,
  type RecordingAssetBody,
  type RecordingAssetView,
  type RecordRecordingInput,
  type RecordRecordingOutput,
  type RecordTranscriptInput,
  type RecordTranscriptOutput,
  type RegisterAgendaItemInput,
  type RegisterAgendaItemOutput,
  type RegisterRoomInput,
  type RegisterRoomOutput,
  type RoomRecord,
  type RoomView,
  type TranscriptBody,
  type TranscriptView,
} from "./types.js";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

// ─── Room (PLAINTEXT) ───────────────────────────────────────────────

export async function registerRoom(e: Etzhayyim, input: RegisterRoomInput): Promise<RegisterRoomOutput> {
  if (!input.roomId || !input.name) return { status: "rejected", error: "missingRequiredFields" };
  const maxParticipants = input.maxParticipants ?? 16;
  if (!isUint(maxParticipants) || maxParticipants < 1) return { status: "rejected", error: "invalidMaxParticipants" };
  const rkey = roomRkey(input.roomId);
  const existing = await e.read<RoomRecord>({ collection: ROOM_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", roomUri: existing.records[0].uri, did: existing.records[0].value.did, roomId: input.roomId };
  }
  const now = new Date().toISOString();
  const did = roomDidFor(input.roomId);
  const record: RoomRecord = {
    did,
    roomId: input.roomId,
    name: input.name,
    topology: input.topology ?? "mesh",
    spatialAudio: input.spatialAudio ?? true,
    maxParticipants,
    status: input.status ?? "active",
    createdAt: now,
  };
  const receipt = await e.write({ collection: ROOM_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", roomUri: receipt.uri, did, roomId: input.roomId };
}

export async function getRoom(e: Etzhayyim, input: GetRoomInput): Promise<GetRoomOutput> {
  if (!input.roomId) return { error: "invalidRoomId" };
  const resp = await e.read<RoomRecord>({ collection: ROOM_COLLECTION, rkey: roomRkey(input.roomId) }).catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r?.value) return { error: "notFound" };
  return { room: { ...r.value, roomUri: r.uri } };
}

export async function listRooms(e: Etzhayyim, input: ListRoomsInput = {}): Promise<ListRoomsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<RoomRecord>({ collection: ROOM_COLLECTION, cursor: input.cursor, limit });
  const items: RoomView[] = resp.records
    .filter((r) => !input.status || r.value.status === input.status)
    .map((r) => ({ ...r.value, roomUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}

/** FK existence check: does a room exist for this roomId? */
async function roomExists(e: Etzhayyim, roomId: string): Promise<boolean> {
  const resp = await e.read<RoomRecord>({ collection: ROOM_COLLECTION, rkey: roomRkey(roomId) }).catch(() => ({ records: [] }));
  return Boolean(resp.records[0]?.value);
}

// ─── Agenda item (PLAINTEXT) ────────────────────────────────────────

export async function registerAgendaItem(e: Etzhayyim, input: RegisterAgendaItemInput): Promise<RegisterAgendaItemOutput> {
  if (!input.agendaItemId || !input.roomId || !input.title) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.ordinal)) return { status: "rejected", error: "invalidOrdinal" };
  if (!isUint(input.allocatedSeconds)) return { status: "rejected", error: "invalidAllocatedSeconds" };
  if (!(await roomExists(e, input.roomId))) return { status: "rejected", error: "roomNotFound" };
  const rkey = agendaRkey(input.agendaItemId);
  const existing = await e.read<AgendaItemRecord>({ collection: AGENDA_COLLECTION, rkey }).catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return { status: "alreadyExists", agendaItemUri: existing.records[0].uri, did: existing.records[0].value.did, agendaItemId: input.agendaItemId };
  }
  const now = new Date().toISOString();
  const did = roomDidFor(input.roomId);
  const record: AgendaItemRecord = {
    did,
    agendaItemId: input.agendaItemId,
    roomId: input.roomId,
    ordinal: input.ordinal,
    title: input.title,
    allocatedSeconds: input.allocatedSeconds,
    createdAt: now,
  };
  const receipt = await e.write({ collection: AGENDA_COLLECTION, record: record as unknown as Record<string, unknown>, rkey });
  return { status: "registered", agendaItemUri: receipt.uri, did, agendaItemId: input.agendaItemId };
}

export async function listAgenda(e: Etzhayyim, input: ListAgendaInput = {}): Promise<ListAgendaOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const resp = await e.read<AgendaItemRecord>({ collection: AGENDA_COLLECTION, cursor: input.cursor, limit });
  const items: AgendaItemView[] = resp.records
    .filter((r) => !input.roomId || r.value.roomId === input.roomId)
    .map((r) => ({ ...r.value, agendaItemUri: r.uri }))
    .sort((a, b) => a.ordinal - b.ordinal);
  return { items, cursor: resp.cursor, total: items.length };
}

// ─── Transcript (E2E-ENCRYPTED, PII) ────────────────────────────────

export async function recordTranscript(e: Etzhayyim, input: RecordTranscriptInput): Promise<RecordTranscriptOutput> {
  if (!input.transcriptId || !input.roomId || !input.speakerDid) return { status: "rejected", error: "missingRequiredFields" };
  if (typeof input.text !== "string" || input.text.length === 0) return { status: "rejected", error: "invalidText" };
  if (!isUint(input.offsetSeconds)) return { status: "rejected", error: "invalidOffsetSeconds" };
  const body: TranscriptBody = {
    transcriptId: input.transcriptId,
    roomId: input.roomId,
    speakerDid: input.speakerDid,
    lang: input.lang || "en",
    text: input.text,
    offsetSeconds: input.offsetSeconds,
    capturedAt: input.capturedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: TRANSCRIPT_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: transcriptRkey(input.transcriptId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, transcriptId: input.transcriptId };
}

async function scanTranscripts(e: Etzhayyim, maxScan: number): Promise<TranscriptView[]> {
  const out: TranscriptView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<TranscriptBody>({ innerType: TRANSCRIPT_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listTranscripts(e: Etzhayyim, input: ListTranscriptsInput = {}): Promise<ListTranscriptsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanTranscripts(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((t) => !input.roomId || t.roomId === input.roomId);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getTranscript(e: Etzhayyim, input: GetTranscriptInput): Promise<GetTranscriptOutput> {
  if (!input.transcriptId) return { error: "invalidTranscriptId" };
  const all = await scanTranscripts(e, DEFAULT_MAX_SCAN);
  const found = all.find((t) => t.transcriptId === input.transcriptId);
  if (!found) return { error: "notFound" };
  return { transcript: found };
}

// ─── Recording asset (E2E-ENCRYPTED, consent + media pointer) ───────

export async function recordRecording(e: Etzhayyim, input: RecordRecordingInput): Promise<RecordRecordingOutput> {
  if (!input.recordingId || !input.roomId || !input.r2Key) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.durationMs)) return { status: "rejected", error: "invalidDurationMs" };
  if (!isPct(input.consentPct)) return { status: "rejected", error: "invalidConsentPct" };
  const body: RecordingAssetBody = {
    recordingId: input.recordingId,
    roomId: input.roomId,
    r2Key: input.r2Key,
    mimeType: input.mimeType || "audio/webm",
    durationMs: input.durationMs,
    consentPct: input.consentPct,
    capturedAt: input.capturedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: RECORDING_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: recordingRkey(input.recordingId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, recordingId: input.recordingId };
}

async function scanRecordings(e: Etzhayyim, maxScan: number): Promise<RecordingAssetView[]> {
  const out: RecordingAssetView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<RecordingAssetBody>({ innerType: RECORDING_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listRecordings(e: Etzhayyim, input: ListRecordingsInput = {}): Promise<ListRecordingsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanRecordings(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((r) => !input.roomId || r.roomId === input.roomId);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

// ─── Action item (E2E-ENCRYPTED, assignee PII) ──────────────────────

export async function recordActionItem(e: Etzhayyim, input: RecordActionItemInput): Promise<RecordActionItemOutput> {
  if (!input.actionItemId || !input.roomId || !input.assigneeDid) return { status: "rejected", error: "missingRequiredFields" };
  if (typeof input.text !== "string" || input.text.length === 0) return { status: "rejected", error: "invalidText" };
  const body: ActionItemBody = {
    actionItemId: input.actionItemId,
    roomId: input.roomId,
    assigneeDid: input.assigneeDid,
    text: input.text,
    status: input.status ?? "open",
    dueAt: input.dueAt ?? "",
    createdAtIso: new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: ACTION_ITEM_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: actionItemRkey(input.actionItemId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, actionItemId: input.actionItemId };
}

async function scanActionItems(e: Etzhayyim, maxScan: number): Promise<ActionItemView[]> {
  const out: ActionItemView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<ActionItemBody>({ innerType: ACTION_ITEM_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listActionItems(e: Etzhayyim, input: ListActionItemsInput = {}): Promise<ListActionItemsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanActionItems(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((a) => !input.roomId || a.roomId === input.roomId);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

// ─── Decision (E2E-ENCRYPTED, confidential governance + ballots) ────

export async function recordDecision(e: Etzhayyim, input: RecordDecisionInput): Promise<RecordDecisionOutput> {
  if (!input.decisionId || !input.roomId || !input.statement) return { status: "rejected", error: "missingRequiredFields" };
  if (!isUint(input.votesFor) || !isUint(input.votesAgainst)) return { status: "rejected", error: "invalidVoteTally" };
  const body: DecisionBody = {
    decisionId: input.decisionId,
    roomId: input.roomId,
    statement: input.statement,
    method: input.method ?? "vote",
    votesFor: input.votesFor,
    votesAgainst: input.votesAgainst,
    ballots: input.ballots ?? {},
    decidedAt: input.decidedAt ?? new Date().toISOString(),
  };
  const receipt = await e.encryptedWrite<Record<string, unknown>>({
    innerType: DECISION_INNER_TYPE,
    record: body as unknown as Record<string, unknown>,
    recipients: input.recipients ?? [],
    rkey: decisionRkey(input.decisionId),
  });
  return { status: "recorded", uri: receipt.uri, keyId: receipt.keyId, decisionId: input.decisionId };
}

async function scanDecisions(e: Etzhayyim, maxScan: number): Promise<DecisionView[]> {
  const out: DecisionView[] = [];
  let cursor: string | undefined;
  while (out.length < maxScan) {
    const page = await e.encryptedRead<DecisionBody>({ innerType: DECISION_INNER_TYPE, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) out.push({ ...r.value, uri: r.uri, sender: r.sender, createdAt: r.createdAt });
    if (!page.cursor || page.records.length === 0) break;
    cursor = page.cursor;
  }
  return out;
}

export async function listDecisions(e: Etzhayyim, input: ListDecisionsInput = {}): Promise<ListDecisionsOutput> {
  const limit = Math.min(input.limit ?? 50, 200);
  const all = await scanDecisions(e, DEFAULT_MAX_SCAN);
  const filtered = all.filter((d) => !input.roomId || d.roomId === input.roomId);
  return { items: filtered.slice(0, limit), total: filtered.length };
}

export async function getDecision(e: Etzhayyim, input: GetDecisionInput): Promise<GetDecisionOutput> {
  if (!input.decisionId) return { error: "invalidDecisionId" };
  const all = await scanDecisions(e, DEFAULT_MAX_SCAN);
  const found = all.find((d) => d.decisionId === input.decisionId);
  if (!found) return { error: "notFound" };
  return { decision: found };
}

// ─── Coverage rollup ────────────────────────────────────────────────

export async function coverage(e: Etzhayyim, input: CoverageInput = {}): Promise<CoverageOutput> {
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);
  const roomsByStatus: Record<string, number> = {};
  let roomCount = 0;
  let cursor: string | undefined;
  while (roomCount < maxScan) {
    const page = await e.read<RoomRecord>({ collection: ROOM_COLLECTION, cursor, limit: PAGE_LIMIT });
    for (const r of page.records) {
      roomsByStatus[r.value.status] = (roomsByStatus[r.value.status] ?? 0) + 1;
      roomCount += 1;
    }
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }

  let agendaItemCount = 0;
  let agendaCursor: string | undefined;
  while (agendaItemCount < maxScan) {
    const apage = await e.read<AgendaItemRecord>({ collection: AGENDA_COLLECTION, cursor: agendaCursor, limit: PAGE_LIMIT });
    agendaItemCount += apage.records.length;
    if (!apage.cursor || apage.records.length < PAGE_LIMIT) break;
    agendaCursor = apage.cursor;
  }

  const transcriptCount = (await scanTranscripts(e, maxScan)).length;
  const recordingCount = (await scanRecordings(e, maxScan)).length;
  const actionItemCount = (await scanActionItems(e, maxScan)).length;
  const decisionCount = (await scanDecisions(e, maxScan)).length;

  return {
    roomCount,
    agendaItemCount,
    transcriptCount,
    recordingCount,
    actionItemCount,
    decisionCount,
    roomsByStatus,
    truncated:
      roomCount >= maxScan ||
      transcriptCount >= maxScan ||
      recordingCount >= maxScan ||
      actionItemCount >= maxScan ||
      decisionCount >= maxScan,
  };
}
