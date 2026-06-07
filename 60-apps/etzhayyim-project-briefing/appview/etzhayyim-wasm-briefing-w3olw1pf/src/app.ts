import {
  asAgentTool,
  createWorkerExport,
  createKyselyDb,
  nowISO,
  str,
  withCapabilityTags,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK,
  resolveHeartbeatCadence,
  createCadenceState,
  createInboxBuffer,
  decodeJson,
  genID,
  nsid,
  parseLexiconInput,
} from "@etzhayyim/kotodama-host-sdk";

const cadenceState = createCadenceState();
const inbox = createInboxBuffer();

let appId = "";
let actorDID = "";

// ─── Graph Labels ───
// Domain-specific SQL node labels for briefing conferencing graph.
// BriefingRoom, BriefingParticipant, BriefingRecording, BriefingTranscript (existing)
// + new labels for domain coverage:
//   BriefingAgenda      — structured meeting agenda items with time allocation
//   BriefingActionItem  — extracted action items from transcripts (assignee + deadline)
//   BriefingSummary     — LLM-generated meeting summary with key decisions
//   BriefingSpeakerTurn — per-speaker talk-time segments for analytics
//   BriefingDecision    — formal decisions made during meeting (vote/consensus)

// ─── Collection Kinds (AT Protocol camelCase) ───
// briefingRoom, briefingParticipant, briefingRecording, briefingTranscript (existing)
// briefingAgenda, briefingActionItem, briefingSummary, briefingSpeakerTurn, briefingDecision

/** Maximum allowed meeting duration in milliseconds (4 hours). */
const MAX_MEETING_DURATION_MS = 4 * 60 * 60 * 1000;
/** Maximum participants before forcing SFU topology. */
const SFU_THRESHOLD = 8;

// ─── Helpers ───

/** Write a domain record (Tier 2 — Hyperdrive direct, ADR-0036). */
async function write(_sdk: HostSDK, kind: string, rec: Record<string, unknown>): Promise<void> {
  function camelToSnake(s: string): string { return s.replace(/[A-Z]/g, c => `_${c.toLowerCase()}`); }
  const table = `vertex_${camelToSnake(kind)}`;
  const ownerDid = actorDID || "did:web:w3olw1pf.etzhayyim.com";
  const rkey = str(rec.recordingId ?? rec.roomId ?? "") || genID();
  const vertex_id = `at://${ownerDid}/com.etzhayyim.apps.briefing.${kind}/${rkey}`;
  const snakeRec = Object.fromEntries(Object.entries(rec).map(([k, v]) => [camelToSnake(k), v]));
  await createKyselyDb().insertInto(table as any).values({ vertex_id, sensitivity_ord: 2, owner_did: ownerDid, actor_id: appId, ...snakeRec }).execute();
}

/** Post a social announcement. */
function post(sdk: HostSDK, text: string): void {
}

// ─── Domain Entity DIDs ───

interface DomainEntity { path: string; displayName: string; description: string; category: string }

const domainEntities: DomainEntity[] = [
  { path: "actor:transcriber", displayName: "Transcriber", description: "Real-time speech-to-text transcription agent", category: "rtc" },
  { path: "actor:translator", displayName: "Translator", description: "Multi-language translation agent for briefing transcripts", category: "nlp" },
  { path: "actor:recorder", displayName: "Recorder", description: "Audio/video recording agent with R2 storage", category: "media" },
  { path: "actor:summarizer", displayName: "Summarizer", description: "Meeting summary and action item extraction agent", category: "nlp" },
];

let entitiesRegistered = false;

/** Register path-based actor DIDs for briefing roles. */
function registerDomainEntities(sdk: HostSDK): void {
  if (entitiesRegistered) return;
  for (const de of domainEntities) {
    try {
      sdk.hostImports.comAtprotoIdentityCreate(de.path, JSON.stringify({
        displayName: de.displayName,
        description: de.description,
        category: de.category,
      }));
    } catch (e) { console.warn(`DID create ${de.path}:`, e); }
  }
  entitiesRegistered = true;
}

// ─── Health & Describe ───

function cmdHealth(): Record<string, unknown> {
  return {
    status: "healthy",
    app: "Briefing",
    nanoid: appId,
    did: actorDID,
    now: nowISO(),
  };
}

function cmdDescribe(): Record<string, unknown> {
  return {
    name: "Briefing",
    did: actorDID,
    nanoid: appId,
    capabilities: [
      "health", "describe", "wave", "echo",
      "createRoom", "joinRoom", "leaveRoom", "listRooms",
      "updatePosition", "sendData",
      "uploadRecording", "saveTranscript",
      "createAgenda", "extractActionItems", "generateSummary",
      "recordSpeakerTurn", "recordDecision",
    ],
    protocols: ["xrpc", "w-protocol", "mcp", "webrtc", "knp"],
    kamiEngine: {
      sdk: "kami-rtc",
      features: ["spatial-audio", "knp-signaling", "mesh-topology", "screen-share"],
    },
  };
}

// ─── Social ───

function cmdWave(sdk: HostSDK, body: Uint8Array): Record<string, unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.wave", body);
  const message = str(args.message ?? "hello");
  post(sdk, `Briefing(${appId}): ${message}`);
  return { ok: true, nanoid: appId };
}

function cmdEcho(_sdk: HostSDK, body: Uint8Array): Record<string, unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.echo", body);
  return { ok: true, nanoid: appId, args };
}

async function dispatcherSecret(env: Record<string, unknown>): Promise<string> {
  const binding = env.DISPATCHER_INTERNAL_SECRET as string | { get?: () => Promise<string> } | undefined;
  if (!binding) return "";
  try {
    return typeof binding === "string" ? binding : await binding.get?.() ?? "";
  } catch {
    return "";
  }
}

async function proxyToDispatcher(sdk: HostSDK, targetNsid: string, body: Uint8Array): Promise<Record<string, unknown>> {
  const env = sdk.env as unknown as Record<string, unknown>;
  const base = str(env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/+$/, "");
  const payload = parseLexiconInput(targetNsid, body) as Record<string, unknown>;
  const headers: Record<string, string> = { "content-type": "application/json" };
  const trust = await dispatcherSecret(env);
  if (trust) headers["x-internal-trust"] = trust;
  const resp = await fetch(`${base}/xrpc/${targetNsid}`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  const text = await resp.text();
  let json: Record<string, unknown>;
  try {
    json = text ? JSON.parse(text) as Record<string, unknown> : {};
  } catch {
    json = { body: text };
  }
  if (!resp.ok) return { ok: false, status: resp.status, ...json };
  return json;
}

// ─── WebRTC Room Management (KAMI Engine kami-rtc) ───
// Design E: edge handles RTC session ergonomics; non-realtime business
// commands are delegated to BPMN-contract/LangServer.

/** Create a new briefing room. Tier 1 social + Tier 2 domain record. */
async function cmdCreateRoom(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.createRoom", body);
  const roomId = str(args.roomId ?? `briefing-${Date.now()}`);
  const name = str(args.name ?? "Briefing Room");
  let topology = str(args.topology ?? "mesh") as "mesh" | "sfu";
  const spatialAudio = args.spatialAudio !== false;
  const maxParticipants = Number(args.maxParticipants ?? 16);
  const actors = (args.actors ?? []) as string[];

  // Business rule: force SFU topology when participant count exceeds mesh threshold
  if (maxParticipants > SFU_THRESHOLD && topology === "mesh") {
    topology = "sfu";
  }

  post(sdk, `Briefing room created: ${name} (${topology}, spatial=${spatialAudio})`);

  await write(sdk, "briefingRoom", {
    roomId,
    name,
    topology,
    spatialAudio,
    maxParticipants,
    status: "active",
    actors: JSON.stringify(actors),
    createdAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
  });

  return {
    ok: true,
    roomId,
    name,
    topology,
    spatialAudio,
    maxParticipants,
    kamiRtcConfig: {
      name,
      max_participants: maxParticipants,
      spatial_audio: spatialAudio,
      topology: topology === "mesh" ? "Mesh" : "Sfu",
      data_channel: true,
      media_constraints: { audio: true, video: true, video_width: 640, video_height: 480, frame_rate: 30 },
    },
  };
}

/** Join a briefing room. Writes participant record as SQL node. */
async function cmdJoinRoom(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.joinRoom", body);
  const roomId = str(args.roomId ?? "");
  const peerId = str(args.peerId ?? "");
  const displayName = str(args.displayName ?? "Anonymous");

  if (!roomId || !peerId) {
    return { ok: false, error: "missing_params", detail: "roomId and peerId required" };
  }

  await write(sdk, "briefingParticipant", {
    roomId,
    peerId,
    displayName,
    action: "join",
    positionX: 0,
    positionY: 0,
    positionZ: 0,
    joinedAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: peerId,
  });

  return { ok: true, roomId, peerId, displayName, joinedAt: nowISO() };
}

/** Leave a briefing room. Writes leave record as SQL node. */
async function cmdLeaveRoom(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.leaveRoom", body);
  const roomId = str(args.roomId ?? "");
  const peerId = str(args.peerId ?? "");

  if (!roomId || !peerId) {
    return { ok: false, error: "missing_params", detail: "roomId and peerId required" };
  }

  await write(sdk, "briefingParticipant", {
    roomId,
    peerId,
    action: "leave",
    leftAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: peerId,
  });

  return { ok: true, roomId, peerId, leftAt: nowISO() };
}

/** List active briefing rooms from graph. */
async function cmdListRooms(): Promise<Record<string, unknown>> {
  const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12

  return { ok: true, rooms: rows, count: rows.length };
}

/** Update participant position for spatial audio. Writes position record as SQL node. */
async function cmdUpdatePosition(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.updatePosition", body);
  const roomId = str(args.roomId ?? "");
  const peerId = str(args.peerId ?? "");
  const x = Number(args.x ?? 0);
  const y = Number(args.y ?? 0);
  const z = Number(args.z ?? 0);

  if (!roomId || !peerId) {
    return { ok: false, error: "missing_params", detail: "roomId and peerId required" };
  }

  await write(sdk, "briefingPosition", {
    roomId,
    peerId,
    positionX: x,
    positionY: y,
    positionZ: z,
    updatedAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: peerId,
  });

  return { ok: true, roomId, peerId, position: [x, y, z] };
}

/** Send data channel message (cursor, annotation, reaction). Writes as SQL node. */
async function cmdSendData(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.sendData", body);
  const roomId = str(args.roomId ?? "");
  const peerId = str(args.peerId ?? "");
  const dataType = str(args.type ?? "cursor");
  const payloadJson = JSON.stringify(args.payload ?? {});

  if (!roomId || !peerId) {
    return { ok: false, error: "missing_params", detail: "roomId and peerId required" };
  }

  await write(sdk, "briefingData", {
    roomId,
    peerId,
    dataType,
    payloadJson,
    sentAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: peerId,
  });

  return { ok: true, roomId, from: peerId, dataType };
}

// ─── Recording & Transcription ───

/** Store recording metadata as SQL node. */
async function cmdUploadRecording(sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.uploadRecording", body);
  const roomId = str(args.roomId ?? "");
  const recordingId = str(args.recordingId ?? genID("rec"));
  const r2Key = str(args.r2Key ?? "");
  const durationMs = Number(args.durationMs ?? 0);
  const mimeType = str(args.mimeType ?? "audio/webm");
  const convoId = str(args.convoId ?? "");

  if (!roomId || !r2Key) {
    return { ok: false, error: "missing_params" };
  }

  await write(sdk, "briefingRecording", {
    roomId,
    recordingId,
    r2Key,
    durationMs,
    mimeType,
    convoId,
    status: "uploaded",
    createdAt: nowISO(),
    org_id: "anon",
    user_id: "anon",
    actor_id: appId,
  });

  return { ok: true, recordingId, r2Key, durationMs };
}

// ─── Reactive Pipeline ───

function handleComAtprotoSyncSubscribeReposCommit(
  _sdk: HostSDK,
  commit: ComAtprotoSyncSubscribeReposCommit,
): { ok: true; detail: string } {
  if (commit.action !== "create") return { ok: true, detail: "skip non-create" };

  const collection = str(commit.collection ?? "");

  if (collection === "com.etzhayyim.apps.briefing.briefingRoom") {
    inbox.inboundCommits.push({ collection, action: "create", ts: Date.now() });
    return { ok: true, detail: `room created: ${collection}` };
  }
  if (collection === "com.etzhayyim.apps.briefing.briefingParticipant") {
    inbox.inboundCommits.push({ collection, action: "create", ts: Date.now() });
    return { ok: true, detail: `participant event: ${collection}` };
  }
  if (collection === "com.etzhayyim.apps.briefing.briefingRecording") {
    return { ok: true, detail: `recording: ${collection}` };
  }
  if (collection === "com.etzhayyim.apps.briefing.briefingTranscript") {
    inbox.inboundCommits.push({ collection, action: "create", ts: Date.now() });
    return { ok: true, detail: `transcript: ${collection}` };
  }
  if (collection === "com.etzhayyim.apps.briefing.briefingActionItem") {
    return { ok: true, detail: `action-item: ${collection}` };
  }
  if (collection === "com.etzhayyim.apps.briefing.briefingSummary") {
    return { ok: true, detail: `summary: ${collection}` };
  }
  if (collection === "com.etzhayyim.apps.briefing.briefingDecision") {
    inbox.inboundCommits.push({ collection, action: "create", ts: Date.now() });
    return { ok: true, detail: `decision: ${collection}` };
  }
  if (collection === "com.etzhayyim.apps.briefing.briefingSpeakerTurn") {
    return { ok: true, detail: `speaker-turn: ${collection}` };
  }
  if (collection === "com.etzhayyim.apps.briefing.briefingAgenda") {
    return { ok: true, detail: `agenda: ${collection}` };
  }

  return { ok: true, detail: `accepted ${collection}` };
}

// ─── Queries ───

/** List recent briefing rooms with participant counts. */
async function cmdListRecentRooms(_sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.listRecentRooms", body);
  const limit = Math.min(Math.max(Number(args.limit ?? 20), 1), 100);
  const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12
  return { ok: true, rooms: rows, count: rows.length };
}

/** Get room details with participants. */
async function cmdGetRoom(_sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.getRoom", body);
  const roomId = str(args.roomId ?? "");
  if (!roomId) return { ok: false, error: "roomId required" };

  // SQL deprecated 2026-04-12 — return empty
  const rooms = [] as Record<string, unknown>[];
  if (rooms.length === 0) return { ok: false, error: "room not found" };

  const participants = [] as Record<string, unknown>[];

  return { ok: true, room: rooms[0], participants, participantCount: participants.length };
}

/** List recordings for a room. */
async function cmdListRecordings(_sdk: HostSDK, body: Uint8Array): Promise<Record<string, unknown>> {
  const args = parseLexiconInput("com.etzhayyim.apps.briefing.listRecordings", body);
  const roomId = str(args.roomId ?? "");
  if (!roomId) return { ok: false, error: "roomId required" };

  const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12
  return { ok: true, recordings: rows, count: rows.length };
}

/** Coverage stats: rooms, participants, recordings, transcripts, agendas, action items, summaries, decisions. */
async function cmdCoverageStats(): Promise<Record<string, unknown>> {
  // SQL deprecated 2026-04-12 — return zero counts
  const [rooms, participants, recordings, transcripts, agendas, actionItems, summaries, decisions] = [[], [], [], [], [], [], [], []] as Record<string, unknown>[][];

  return {
    ok: true,
    rooms: Number(rooms[0]?.cnt ?? 0),
    participants: Number(participants[0]?.cnt ?? 0),
    recordings: Number(recordings[0]?.cnt ?? 0),
    transcripts: Number(transcripts[0]?.cnt ?? 0),
    agendas: Number(agendas[0]?.cnt ?? 0),
    actionItems: Number(actionItems[0]?.cnt ?? 0),
    summaries: Number(summaries[0]?.cnt ?? 0),
    decisions: Number(decisions[0]?.cnt ?? 0),
  };
}

// ─── App Configuration ───

const configuredApps = new WeakSet<object>();

function configureApp(sdk: HostSDK): void {
  const app = sdk.app;
  if (configuredApps.has(app as object)) return;

  // Core commands
  app
    .command(nsid("com.etzhayyim.apps.briefing.health"), async () => cmdHealth(), asAgentTool("Briefing health check"), withCapabilityTags("diagnostics", "briefing"))
    .command(nsid("com.etzhayyim.apps.briefing.describe"), async () => cmdDescribe(), asAgentTool("Describe briefing app"), withCapabilityTags("meta", "briefing"))
    .command(nsid("com.etzhayyim.apps.briefing.wave"), async (_ctx, body) => cmdWave(sdk, body), asAgentTool("Post briefing status"), withCapabilityTags("social", "briefing"))
    .command(nsid("com.etzhayyim.apps.briefing.echo"), async (_ctx, body) => cmdEcho(sdk, body), asAgentTool("Echo payload"), withCapabilityTags("utility", "briefing"));

  // WebRTC room commands (KAMI Engine kami-rtc, Design E stateless)
  app
    .command(nsid("com.etzhayyim.apps.briefing.createRoom"), async (_ctx, body) => cmdCreateRoom(sdk, body), asAgentTool("Create WebRTC briefing room with KAMI spatial audio"), withCapabilityTags("rtc", "briefing", "spatialAudio"))
    .command(nsid("com.etzhayyim.apps.briefing.joinRoom"), async (_ctx, body) => cmdJoinRoom(sdk, body), asAgentTool("Join existing briefing room"), withCapabilityTags("rtc", "briefing"))
    .command(nsid("com.etzhayyim.apps.briefing.leaveRoom"), async (_ctx, body) => cmdLeaveRoom(sdk, body), asAgentTool("Leave briefing room"), withCapabilityTags("rtc", "briefing"))
    .command(nsid("com.etzhayyim.apps.briefing.listRooms"), async () => cmdListRooms(), asAgentTool("List active briefing rooms"), withCapabilityTags("rtc", "briefing"))
    .command(nsid("com.etzhayyim.apps.briefing.updatePosition"), async (_ctx, body) => cmdUpdatePosition(sdk, body), asAgentTool("Update spatial audio position"), withCapabilityTags("rtc", "spatialAudio"))
    .command(nsid("com.etzhayyim.apps.briefing.sendData"), async (_ctx, body) => cmdSendData(sdk, body), asAgentTool("Send data channel message"), withCapabilityTags("rtc", "dataChannel"));

  // Recording & transcription commands
  app
    .command(nsid("com.etzhayyim.apps.briefing.uploadRecording"), async (_ctx, body) => cmdUploadRecording(sdk, body), asAgentTool("Store recording metadata"), withCapabilityTags("recording", "briefing"))
    .command(nsid("com.etzhayyim.apps.briefing.saveTranscript"), async (_ctx, body) => proxyToDispatcher(sdk, "com.etzhayyim.apps.briefing.saveTranscript", body), asAgentTool("Save transcript and auto-translate"), withCapabilityTags("transcription", "briefing", "bpmn"));

  // Agenda, action items, summary, speaker analytics, decisions
  app
    .command(nsid("com.etzhayyim.apps.briefing.createAgenda"), async (_ctx, body) => proxyToDispatcher(sdk, "com.etzhayyim.apps.briefing.createAgenda", body), asAgentTool("Create time-boxed meeting agenda"), withCapabilityTags("agenda", "briefing", "bpmn"))
    .command(nsid("com.etzhayyim.apps.briefing.extractActionItems"), async (_ctx, body) => proxyToDispatcher(sdk, "com.etzhayyim.apps.briefing.extractActionItems", body), asAgentTool("Extract action items from transcript"), withCapabilityTags("actionItem", "briefing", "nlp", "bpmn"))
    .command(nsid("com.etzhayyim.apps.briefing.generateSummary"), async (_ctx, body) => proxyToDispatcher(sdk, "com.etzhayyim.apps.briefing.generateSummary", body), asAgentTool("Generate meeting summary from transcript"), withCapabilityTags("summary", "briefing", "nlp", "bpmn"))
    .command(nsid("com.etzhayyim.apps.briefing.recordSpeakerTurn"), async (_ctx, body) => proxyToDispatcher(sdk, "com.etzhayyim.apps.briefing.recordSpeakerTurn", body), asAgentTool("Record speaker turn for talk-time analytics"), withCapabilityTags("analytics", "briefing", "bpmn"))
    .command(nsid("com.etzhayyim.apps.briefing.recordDecision"), async (_ctx, body) => proxyToDispatcher(sdk, "com.etzhayyim.apps.briefing.recordDecision", body), asAgentTool("Record formal meeting decision"), withCapabilityTags("decision", "briefing", "governance", "bpmn"));

  // Query commands
  app
    .command(nsid("com.etzhayyim.apps.briefing.listRecentRooms"), async (_ctx, body) => cmdListRecentRooms(sdk, body), asAgentTool("List recent briefing rooms"), withCapabilityTags("query", "briefing"))
    .command(nsid("com.etzhayyim.apps.briefing.getRoom"), async (_ctx, body) => cmdGetRoom(sdk, body), asAgentTool("Get room details with participants"), withCapabilityTags("query", "briefing"))
    .command(nsid("com.etzhayyim.apps.briefing.listRecordings"), async (_ctx, body) => cmdListRecordings(sdk, body), asAgentTool("List recordings for a room"), withCapabilityTags("query", "recording"))
    .command(nsid("com.etzhayyim.apps.briefing.coverageStats"), async () => cmdCoverageStats(), asAgentTool("Briefing coverage statistics"), withCapabilityTags("coverage", "stats"));

  configuredApps.add(app as object);
}

export { handleComAtprotoSyncSubscribeReposCommit };

export async function runHeartbeat(sdk: HostSDK): Promise<{ ok: boolean; actions: Array<Record<string, unknown>> }> {
  const actions: Array<Record<string, unknown>> = [];
  const ts = nowISO();

  // Resolve joucho cadence with correct actorDID
  const cadence = await resolveHeartbeatCadence(actorDID, cadenceState, inbox);
  actions.push({
    action: "cadenceResolved",
    mood: cadence.mood,
    shouldPost: cadence.shouldPost,
    shouldEngage: cadence.shouldEngage,
    shouldDrill: cadence.shouldDrill,
    reason: cadence.reason,
    ts,
  });

  // shouldPost: coverage stats or domain insight
  if (cadence.shouldPost && cadence.contentSource.type !== "none") {
    try {
      const stats = await cmdCoverageStats();
      const text = `Briefing status: ${stats.rooms} rooms, ${stats.participants} participants, ${stats.recordings} recordings, ${stats.transcripts} transcripts`;
      post(sdk, text);
      actions.push({ action: "post", source: "coverageStats", ts });
    } catch (e) {
      console.warn("heartbeat post:", e);
      actions.push({ action: "postFailed", error: String(e), ts });
    }
  }

  // shouldDrill: self-information gathering (kyumei-koji)

  // shouldEngage: follower rewards

  if (actions.length === 1) actions.push({ action: "noop", mood: cadence.mood, ts });
  return { ok: true, actions };
}

export default createWorkerExport((sdk) => {
  appId = sdk.pds.selfNanoid ?? "";
  actorDID = sdk.pds.selfRepo ?? "";
  registerDomainEntities(sdk);
  configureApp(sdk);
});
