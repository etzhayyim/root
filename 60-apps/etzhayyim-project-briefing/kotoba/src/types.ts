/**
 * briefing kotoba — meeting / WebRTC briefing platform, kotoba-E2E split.
 *
 * Per ADR-2606011400 (Consensys product-front) + ADR-2605172400 (3-axis) +
 * ADR-2605181100 (kotoba E2E encrypted-record envelope) + ADR-0014 (PII Tier 3).
 * Founder directive 2026-06-03: maximal migration — front everything that can
 * move; only the irreducible regulated EXECUTION stays etzhayyim.
 *
 * SPLIT:
 *   PUBLIC (plaintext AT records via sdk.write/sdk.read) — non-sensitive meeting
 *   STRUCTURE/ops facts: room catalog (topology / capacity / status) and the
 *   time-boxed agenda. These are reference/catalog metadata, no participant PII.
 *
 *   PRIVATE / PII Tier 3 (kotoba E2E via sdk.encryptedWrite/Read,
 *   com.etzhayyim.encrypted.record) — meeting CONTENT and per-person data:
 *   transcripts (spoken words = PII), recording-asset metadata (consent + R2
 *   pointer to a PII recording), action items (assignee PII + private text), and
 *   formal decisions (confidential governance + per-voter ballots). Read-cap =
 *   owner DID + explicit recipients, so meeting content lives on-substrate
 *   encrypted, never etzhayyim-resident plaintext.
 *
 *   STAYS etzhayyim (consumed via consent-capability) — the irreducible regulated
 *   EXECUTION only, NOT a collection: the R2/B2 recording-blob ARCHIVE (raw
 *   audio/video media that physically cannot fit AT PDS) plus the GPU/LLM
 *   INFERENCE acts (Whisper STT, translation, summarization, action-item
 *   extraction). We FRONT the resulting records E2E; the heavy media custody +
 *   inference CALLS stay etzhayyim.
 *
 * AT-Lexicon: no float (durations/seconds/counts are integers; talkRatio and
 * consent are integer 0-100; r2Key/durations carried as integers or strings).
 */

// ─── Plaintext public collections ───────────────────────────────────
export const ROOM_COLLECTION = "com.etzhayyim.apps.briefing.room";
export const AGENDA_COLLECTION = "com.etzhayyim.apps.briefing.agendaItem";

// ─── E2E inner-type NSIDs (body shape inside the encrypted envelope) ─
export const TRANSCRIPT_INNER_TYPE = "com.etzhayyim.apps.briefing.transcript";
export const RECORDING_INNER_TYPE = "com.etzhayyim.apps.briefing.recordingAsset";
export const ACTION_ITEM_INNER_TYPE = "com.etzhayyim.apps.briefing.actionItem";
export const DECISION_INNER_TYPE = "com.etzhayyim.apps.briefing.decision";

export const BRIEFING_DID_PREFIX = "did:web:briefing.etzhayyim.com:" as const;

export type RoomTopology = "mesh" | "sfu";
export type RoomStatus = "active" | "closed";
export type DecisionMethod = "vote" | "consensus";
export type ActionItemStatus = "open" | "done" | "cancelled";

// ─── Room (PLAINTEXT, public catalog metadata) ──────────────────────

export interface RoomRecord {
  did: string;
  roomId: string;
  name: string;
  topology: RoomTopology;
  spatialAudio: boolean;
  maxParticipants: number;
  status: RoomStatus;
  createdAt: string;
}
export interface RoomView extends RoomRecord {
  roomUri: string;
}
export interface RegisterRoomInput {
  roomId: string;
  name: string;
  topology?: RoomTopology;
  spatialAudio?: boolean;
  maxParticipants?: number;
  status?: RoomStatus;
}
export interface RegisterRoomOutput {
  status: "registered" | "alreadyExists" | "rejected";
  roomUri?: string;
  did?: string;
  roomId?: string;
  error?: string;
}
export interface GetRoomInput {
  roomId: string;
}
export interface GetRoomOutput {
  room?: RoomView;
  error?: string;
}
export interface ListRoomsInput {
  status?: RoomStatus;
  limit?: number;
  cursor?: string;
}
export interface ListRoomsOutput {
  items: RoomView[];
  cursor?: string;
  total: number;
}

// ─── Agenda item (PLAINTEXT, public meeting structure) ──────────────

export interface AgendaItemRecord {
  did: string;
  agendaItemId: string;
  roomId: string;
  ordinal: number;
  title: string;
  /** time allocation in whole seconds (integer; no float). */
  allocatedSeconds: number;
  createdAt: string;
}
export interface AgendaItemView extends AgendaItemRecord {
  agendaItemUri: string;
}
export interface RegisterAgendaItemInput {
  agendaItemId: string;
  roomId: string;
  ordinal: number;
  title: string;
  allocatedSeconds: number;
}
export interface RegisterAgendaItemOutput {
  status: "registered" | "alreadyExists" | "rejected";
  agendaItemUri?: string;
  did?: string;
  agendaItemId?: string;
  error?: string;
}
export interface ListAgendaInput {
  roomId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListAgendaOutput {
  items: AgendaItemView[];
  cursor?: string;
  total: number;
}

// ─── Transcript (E2E-ENCRYPTED, PII spoken content) ─────────────────

export interface TranscriptBody {
  transcriptId: string;
  roomId: string;
  /** speaker peer/DID — per-person, kept inside the envelope. */
  speakerDid: string;
  lang: string;
  /** spoken words (PII). */
  text: string;
  /** offset from meeting start, whole seconds (integer). */
  offsetSeconds: number;
  capturedAt: string;
}
export interface TranscriptView extends TranscriptBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordTranscriptInput {
  transcriptId: string;
  roomId: string;
  speakerDid: string;
  lang: string;
  text: string;
  offsetSeconds: number;
  capturedAt?: string;
  recipients?: string[];
}
export interface RecordTranscriptOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  transcriptId?: string;
  error?: string;
}
export interface ListTranscriptsInput {
  roomId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListTranscriptsOutput {
  items: TranscriptView[];
  cursor?: string;
  total: number;
}
export interface GetTranscriptInput {
  transcriptId: string;
}
export interface GetTranscriptOutput {
  transcript?: TranscriptView;
  error?: string;
}

// ─── Recording asset (E2E-ENCRYPTED, consent + PII media pointer) ───
// NOTE: the raw audio/video BLOB stays in the etzhayyim R2/B2 archive (irreducible
// large-media custody). Only the consent-bearing pointer record fronts E2E.

export interface RecordingAssetBody {
  recordingId: string;
  roomId: string;
  /** opaque pointer into the etzhayyim-resident R2/B2 media archive. */
  r2Key: string;
  mimeType: string;
  /** whole milliseconds (integer). */
  durationMs: number;
  /** participant consent coverage, integer 0-100 (% of participants). */
  consentPct: number;
  capturedAt: string;
}
export interface RecordingAssetView extends RecordingAssetBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordRecordingInput {
  recordingId: string;
  roomId: string;
  r2Key: string;
  mimeType?: string;
  durationMs: number;
  consentPct: number;
  capturedAt?: string;
  recipients?: string[];
}
export interface RecordRecordingOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  recordingId?: string;
  error?: string;
}
export interface ListRecordingsInput {
  roomId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListRecordingsOutput {
  items: RecordingAssetView[];
  cursor?: string;
  total: number;
}

// ─── Action item (E2E-ENCRYPTED, assignee PII + private text) ───────

export interface ActionItemBody {
  actionItemId: string;
  roomId: string;
  assigneeDid: string;
  text: string;
  status: ActionItemStatus;
  /** optional ISO deadline. */
  dueAt: string;
  createdAtIso: string;
}
export interface ActionItemView extends ActionItemBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordActionItemInput {
  actionItemId: string;
  roomId: string;
  assigneeDid: string;
  text: string;
  status?: ActionItemStatus;
  dueAt?: string;
  recipients?: string[];
}
export interface RecordActionItemOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  actionItemId?: string;
  error?: string;
}
export interface ListActionItemsInput {
  roomId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListActionItemsOutput {
  items: ActionItemView[];
  cursor?: string;
  total: number;
}

// ─── Decision (E2E-ENCRYPTED, confidential governance + ballots) ────

export interface DecisionBody {
  decisionId: string;
  roomId: string;
  statement: string;
  method: DecisionMethod;
  /** integer tallies. */
  votesFor: number;
  votesAgainst: number;
  /** per-voter ballots (PII), DID → "for" | "against" | "abstain". */
  ballots: Record<string, string>;
  decidedAt: string;
}
export interface DecisionView extends DecisionBody {
  uri: string;
  sender: string;
  createdAt: string;
}
export interface RecordDecisionInput {
  decisionId: string;
  roomId: string;
  statement: string;
  method?: DecisionMethod;
  votesFor: number;
  votesAgainst: number;
  ballots?: Record<string, string>;
  decidedAt?: string;
  recipients?: string[];
}
export interface RecordDecisionOutput {
  status: "recorded" | "rejected";
  uri?: string;
  keyId?: string;
  decisionId?: string;
  error?: string;
}
export interface ListDecisionsInput {
  roomId?: string;
  limit?: number;
  cursor?: string;
}
export interface ListDecisionsOutput {
  items: DecisionView[];
  cursor?: string;
  total: number;
}
export interface GetDecisionInput {
  decisionId: string;
}
export interface GetDecisionOutput {
  decision?: DecisionView;
  error?: string;
}

// ─── Coverage rollup ────────────────────────────────────────────────

export interface CoverageInput {
  maxScan?: number;
}
export interface CoverageOutput {
  roomCount?: number;
  agendaItemCount?: number;
  transcriptCount?: number;
  recordingCount?: number;
  actionItemCount?: number;
  decisionCount?: number;
  roomsByStatus?: Record<string, number>;
  truncated?: boolean;
  error?: string;
}

// ─── Validation + helpers ───────────────────────────────────────────

export function isUint(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0;
}
export function isPct(n: unknown): n is number {
  return typeof n === "number" && Number.isInteger(n) && n >= 0 && n <= 100;
}
export function roomDidFor(id: string): string {
  return `${BRIEFING_DID_PREFIX}room:${id.toLowerCase()}`;
}
function slug(id: string): string {
  return id.toLowerCase().replace(/[^a-z0-9]+/g, "-");
}
export function roomRkey(id: string): string {
  return `room-${slug(id)}`;
}
export function agendaRkey(id: string): string {
  return `agenda-${slug(id)}`;
}
export function transcriptRkey(id: string): string {
  return `transcript-${slug(id)}`;
}
export function recordingRkey(id: string): string {
  return `recording-${slug(id)}`;
}
export function actionItemRkey(id: string): string {
  return `action-${slug(id)}`;
}
export function decisionRkey(id: string): string {
  return `decision-${slug(id)}`;
}
