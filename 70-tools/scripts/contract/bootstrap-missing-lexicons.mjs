#!/usr/bin/env node
/**
 * bootstrap-missing-lexicons.mjs
 *
 * Generates AT Protocol Lexicon JSON files for XRPC method NSIDs
 * that exist in PDS handlers but lack Lexicon definitions.
 *
 * Skips files that already exist.
 */

import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";

const BASE = join(import.meta.dirname, "../../../00-contracts/lexicons");

// ---------------------------------------------------------------------------
// Schema helpers
// ---------------------------------------------------------------------------

/** Build a property schema entry */
function str() { return { type: "string" }; }
function int() { return { type: "integer" }; }
function bool() { return { type: "boolean" }; }
function objArr() { return { type: "array", items: { type: "object" } }; }
function strArr() { return { type: "array", items: { type: "string" } }; }
function obj() { return { type: "object" }; }

/**
 * Build a procedure lexicon.
 * @param {string} id  NSID
 * @param {Record<string,object>} inputProps
 * @param {string[]} inputRequired
 * @param {Record<string,object>} outputProps
 * @param {string[]} outputRequired
 */
function procedure(id, inputProps, inputRequired, outputProps, outputRequired) {
  const input = {
    encoding: "application/json",
    schema: { type: "object", properties: inputProps },
  };
  if (inputRequired.length) input.schema.required = inputRequired;

  const output = {
    encoding: "application/json",
    schema: { type: "object", properties: outputProps },
  };
  if (outputRequired.length) output.schema.required = outputRequired;

  return { lexicon: 1, id, defs: { main: { type: "procedure", input, output } } };
}

/**
 * Build a query lexicon.
 * @param {string} id  NSID
 * @param {Record<string,object>} paramProps
 * @param {string[]} paramRequired
 * @param {Record<string,object>} outputProps
 * @param {string[]} outputRequired
 */
function query(id, paramProps, paramRequired, outputProps, outputRequired) {
  const parameters = { type: "params", properties: paramProps };
  if (paramRequired.length) parameters.required = paramRequired;

  const output = {
    encoding: "application/json",
    schema: { type: "object", properties: outputProps },
  };
  if (outputRequired.length) output.schema.required = outputRequired;

  return { lexicon: 1, id, defs: { main: { type: "query", parameters, output } } };
}

// ---------------------------------------------------------------------------
// Definitions — Procedures
// ---------------------------------------------------------------------------

const procedures = [
  procedure("com.etzhayyim.agent.chat",
    { messages: objArr(), model: str(), stream: bool() },
    ["messages"],
    { response: str() },
    ["response"]),

  procedure("com.etzhayyim.agent.registerTools",
    { tools: objArr() },
    ["tools"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.pds.invoke",
    { did: str(), method: str(), params: obj() },
    ["did", "method"],
    { result: obj() },
    ["result"]),

  procedure("com.etzhayyim.pds.putProfile",
    { displayName: str(), description: str(), avatar: str() },
    [],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.pds.importRepo",
    { data: str() },
    ["data"],
    { imported: bool() },
    ["imported"]),

  procedure("com.etzhayyim.pds.registerSyncApp",
    { nanoid: str() },
    ["nanoid"],
    { registered: bool() },
    ["registered"]),

  procedure("com.etzhayyim.identity.register",
    { nanoid: str(), displayName: str() },
    ["nanoid"],
    { did: str(), registered: bool() },
    ["did", "registered"]),

  procedure("com.etzhayyim.governance.approveFollowRequest",
    { did: str() },
    ["did"],
    { approved: bool(), did: str() },
    ["approved", "did"]),

  procedure("com.etzhayyim.governance.rejectFollowRequest",
    { did: str() },
    ["did"],
    { rejected: bool(), did: str() },
    ["rejected", "did"]),

  procedure("com.etzhayyim.governance.approveAllFollowRequests",
    {},
    [],
    { approvedAll: bool() },
    ["approvedAll"]),

  procedure("com.etzhayyim.governance.registerManifest",
    { manifestJson: str() },
    ["manifestJson"],
    { registered: bool(), appId: str(), policyCount: int() },
    ["registered", "appId", "policyCount"]),

  procedure("com.etzhayyim.governance.registerRoleBindings",
    { appNanoid: str(), roles: objArr() },
    ["appNanoid", "roles"],
    { registered: bool(), bound: int() },
    ["registered", "bound"]),

  procedure("com.etzhayyim.governance.createLabel",
    { label: obj() },
    ["label"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.convo.edit",
    { convoId: str(), messageId: str(), text: str() },
    ["convoId", "messageId", "text"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.convo.send",
    { convoId: str(), text: str(), kind: str(), contentType: str() },
    ["convoId", "text"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.convo.search",
    { q: str(), convoId: str(), limit: int() },
    ["q"],
    { results: objArr() },
    ["results"]),

  procedure("com.etzhayyim.convo.forwardMessage",
    { convoId: str(), targetConvoId: str(), messageId: str() },
    ["convoId", "targetConvoId", "messageId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.convo.pinMessage",
    { convoId: str(), messageId: str() },
    ["convoId", "messageId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.convo.unpinMessage",
    { convoId: str(), messageId: str() },
    ["convoId", "messageId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.convo.inviteMember",
    { convoId: str(), memberDid: str() },
    ["convoId", "memberDid"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.convo.updateMemberRole",
    { convoId: str(), memberDid: str(), role: str() },
    ["convoId", "memberDid", "role"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.signal.ensureDevice",
    { deviceId: str(), deviceName: str() },
    [],
    { deviceId: str(), did: str(), provisioned: bool() },
    ["deviceId", "did", "provisioned"]),

  procedure("com.etzhayyim.signal.revokeDevice",
    { deviceId: str() },
    ["deviceId"],
    { deviceId: str(), revoked: bool() },
    ["deviceId", "revoked"]),

  procedure("com.etzhayyim.signal.renameDevice",
    { deviceId: str(), name: str() },
    ["deviceId", "name"],
    { deviceId: str(), name: str() },
    ["deviceId", "name"]),

  procedure("com.etzhayyim.signal.registerPrekeys",
    { identityKey: str(), signedPrekey: obj(), oneTimePrekeys: objArr(), deviceId: str() },
    ["identityKey", "signedPrekey", "oneTimePrekeys"],
    { rkey: str(), registered: bool(), otkCount: int() },
    ["rkey", "registered", "otkCount"]),

  procedure("com.etzhayyim.signal.replenishOtpks",
    { oneTimePrekeys: objArr(), deviceId: str() },
    ["oneTimePrekeys"],
    { replenished: bool(), count: int() },
    ["replenished", "count"]),

  procedure("com.etzhayyim.signal.setEncryption",
    { convoId: str(), mode: str() },
    ["convoId"],
    { convoId: str(), encryption: str() },
    ["convoId", "encryption"]),

  procedure("com.etzhayyim.signal.verifyIdentity",
    { did: str(), fingerprint: str() },
    ["did", "fingerprint"],
    { did: str(), verified: bool() },
    ["did", "verified"]),

  procedure("com.etzhayyim.signal.rotateGroupKey",
    { convoId: str() },
    ["convoId"],
    { convoId: str(), rotated: bool(), rkey: str() },
    ["convoId", "rotated", "rkey"]),

  procedure("com.etzhayyim.rtc.scheduleMeeting",
    { title: str(), scheduledAt: str(), participants: strArr() },
    ["title"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.rtc.joinMeeting",
    { meetingId: str() },
    ["meetingId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.rtc.admitParticipant",
    { meetingId: str(), participantDid: str() },
    ["meetingId", "participantDid"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.rtc.createBreakout",
    { meetingId: str(), name: str() },
    ["meetingId", "name"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.rtc.startRecording",
    { meetingId: str(), action: str() },
    ["meetingId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.rtc.raiseHand",
    { meetingId: str(), raised: bool() },
    ["meetingId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.rtc.openHuddle",
    { convoId: str() },
    ["convoId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.rtc.shareScreen",
    { meetingId: str(), sharing: bool() },
    ["meetingId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.stream.subscribe",
    { topics: strArr() },
    ["topics"],
    { subscriptionId: str() },
    ["subscriptionId"]),

  procedure("com.etzhayyim.stream.openStream",
    { topics: strArr() },
    [],
    { streamId: str() },
    ["streamId"]),

  procedure("com.etzhayyim.stream.closeStream",
    { streamId: str() },
    ["streamId"],
    { closed: bool() },
    ["closed"]),

  procedure("com.etzhayyim.apps.llm.chatCompletions",
    { messages: objArr(), model: str(), maxTokens: int() },
    ["messages"],
    { choices: objArr() },
    ["choices"]),

  procedure("com.etzhayyim.apps.llm.converse",
    { message: str(), model: str() },
    ["message"],
    { response: str() },
    ["response"]),

  procedure("com.etzhayyim.apps.llm.generateImage",
    { prompt: str(), model: str() },
    ["prompt"],
    { url: str() },
    ["url"]),

  procedure("com.etzhayyim.apps.celler.provisionEsim",
    { did: str(), dataPlan: str() },
    ["did"],
    { iccid: str(), status: str() },
    ["iccid", "status"]),

  procedure("com.etzhayyim.apps.celler.activateEsim",
    { iccid: str() },
    ["iccid"],
    { status: str(), iccid: str() },
    ["status", "iccid"]),

  procedure("com.etzhayyim.apps.celler.suspendEsim",
    { iccid: str() },
    ["iccid"],
    { status: str(), iccid: str() },
    ["status", "iccid"]),

  procedure("com.etzhayyim.apps.yoro.activity.markSeen",
    {},
    [],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.murakumo.trainExperts",
    { dataDir: str() },
    ["dataDir"],
    { status: str() },
    ["status"]),

  procedure("com.etzhayyim.projector.branchConvo",
    { convoId: str(), name: str() },
    ["convoId"],
    { branchConvoId: str() },
    ["branchConvoId"]),

  procedure("com.etzhayyim.projector.exploreThoughts",
    { convoId: str(), question: str() },
    ["convoId"],
    { reply: str(), messages: objArr() },
    ["reply", "messages"]),

  procedure("com.etzhayyim.projector.consistentAnswer",
    { convoId: str(), question: str() },
    ["convoId"],
    { answer: str() },
    ["answer"]),

  procedure("com.etzhayyim.projector.addReflection",
    { convoId: str() },
    ["convoId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("com.etzhayyim.projector.moveProject",
    { convoId: str(), targetParentUri: str() },
    ["convoId"],
    { status: str() },
    ["status"]),

  procedure("com.etzhayyim.projector.resolveProjectEmail",
    { email: str() },
    ["email"],
    { convoId: str() },
    ["convoId"]),

];

// ---------------------------------------------------------------------------
// Definitions — Queries
// ---------------------------------------------------------------------------

const queries = [
  query("com.etzhayyim.pds.query",
    { statement: str(), parameters: obj() },
    ["statement"],
    { rows: objArr() },
    ["rows"]),

  query("com.etzhayyim.pds.getActorProfile",
    { did: str(), handle: str() },
    [],
    { profile: obj() },
    ["profile"]),

  query("com.etzhayyim.pds.getProfile",
    { did: str() },
    [],
    { profile: obj() },
    ["profile"]),

  query("com.etzhayyim.pds.getAppPreview",
    { nanoid: str() },
    ["nanoid"],
    { app: obj() },
    ["app"]),

  query("com.etzhayyim.pds.getEntityGraph",
    { did: str(), depth: int() },
    ["did"],
    { nodes: objArr(), edges: objArr() },
    ["nodes", "edges"]),

  query("com.etzhayyim.pds.exportRepo",
    { did: str() },
    [],
    { data: str() },
    ["data"]),

  query("com.etzhayyim.pds.listHeartbeatApps",
    { limit: int() },
    [],
    { apps: objArr() },
    ["apps"]),

  query("com.etzhayyim.identity.resolve",
    { did: str(), handle: str() },
    [],
    { did: str(), handle: str() },
    ["did", "handle"]),

  query("com.etzhayyim.identity.list",
    { limit: int(), cursor: str() },
    [],
    { identities: objArr(), cursor: str() },
    ["identities"]),

  query("com.etzhayyim.identity.getEngagement",
    { did: str() },
    [],
    { engagement: obj() },
    ["engagement"]),

  query("com.etzhayyim.identity.pullFeed",
    { did: str(), limit: int() },
    [],
    { feed: objArr() },
    ["feed"]),

  query("com.etzhayyim.governance.queryLabels",
    { limit: int() },
    [],
    { labels: objArr(), cursor: str() },
    ["labels"]),

  query("com.etzhayyim.convo.getThread",
    { convoId: str(), messageId: str() },
    ["convoId", "messageId"],
    { thread: objArr() },
    ["thread"]),

  query("com.etzhayyim.convo.listMembers",
    { convoId: str() },
    ["convoId"],
    { members: objArr() },
    ["members"]),

  query("com.etzhayyim.convo.getUnread",
    {},
    [],
    { count: int() },
    ["count"]),

  query("com.etzhayyim.convo.listPresence",
    { convoId: str() },
    ["convoId"],
    { presence: objArr() },
    ["presence"]),

  query("com.etzhayyim.convo.listPublicConvos",
    { limit: int(), cursor: str() },
    [],
    { convos: objArr(), cursor: str() },
    ["convos"]),

  query("com.etzhayyim.convo.getProfile",
    {},
    [],
    { profile: obj() },
    ["profile"]),

  query("com.etzhayyim.convo.fetchBlocks",
    { convoId: str() },
    [],
    { blocks: objArr() },
    ["blocks"]),

  query("com.etzhayyim.signal.listDevices",
    {},
    [],
    { devices: objArr() },
    ["devices"]),

  query("com.etzhayyim.signal.getIdentityFingerprint",
    { did: str() },
    [],
    { did: str(), fingerprint: str() },
    ["did", "fingerprint"]),

  query("com.etzhayyim.signal.getPrekeyBundle",
    { did: str() },
    ["did"],
    { bundle: obj() },
    ["bundle"]),

  query("com.etzhayyim.signal.getPrekeyBundles",
    { did: str() },
    ["did"],
    { bundles: objArr() },
    ["bundles"]),


  query("com.etzhayyim.stream.readFrames",
    { streamId: str(), limit: int() },
    ["streamId"],
    { frames: objArr() },
    ["frames"]),

  query("com.etzhayyim.apps.celler.getEsimProfile",
    {},
    [],
    { profiles: objArr() },
    ["profiles"]),

  query("com.etzhayyim.apps.yoro.activity.listActivities",
    { limit: int(), cursor: str(), objectTypes: str(), actorDid: str() },
    [],
    { events: objArr(), cursor: str() },
    ["events"]),

  query("com.etzhayyim.apps.yoro.activity.getActivityTrace",
    { objectType: str(), objectId: str() },
    ["objectType", "objectId"],
    { trace: objArr() },
    ["trace"]),

  query("com.etzhayyim.projector.loadProjectChat",
    { convoId: str() },
    ["convoId"],
    { convoId: str(), messages: objArr(), members: objArr() },
    ["convoId", "messages", "members"]),

  query("com.etzhayyim.projector.listProjectTree",
    { convoId: str(), maxDepth: int() },
    ["convoId"],
    { tree: objArr() },
    ["tree"]),

  query("com.etzhayyim.projector.listBranches",
    { convoId: str(), offset: int(), limit: int() },
    ["convoId"],
    { branches: objArr() },
    ["branches"]),

  query("com.etzhayyim.projector.listReflections",
    { convoId: str(), offset: int(), limit: int() },
    ["convoId"],
    { reflections: objArr() },
    ["reflections"]),

  query("com.etzhayyim.projector.getProjectUnreadCounts",
    { convoId: str() },
    [],
    { counts: objArr() },
    ["counts"]),

  query("com.etzhayyim.projector.listProjectNotifications",
    { limit: int(), cursor: str() },
    [],
    { notifications: objArr(), cursor: str() },
    ["notifications"]),
];

// ---------------------------------------------------------------------------
// Write files
// ---------------------------------------------------------------------------

const allDefs = [...procedures, ...queries];
let created = 0;
let skipped = 0;

for (const def of allDefs) {
  const segments = def.id.split(".");
  const filename = segments.pop() + ".json";
  const dir = join(BASE, ...segments);
  const filepath = join(dir, filename);

  if (existsSync(filepath)) {
    console.log(`SKIP (exists): ${filepath}`);
    skipped++;
    continue;
  }

  mkdirSync(dir, { recursive: true });
  writeFileSync(filepath, JSON.stringify(def, null, 2) + "\n");
  console.log(`CREATED: ${filepath}`);
  created++;
}

console.log(`\nDone. Created: ${created}, Skipped: ${skipped}, Total definitions: ${allDefs.length}`);
