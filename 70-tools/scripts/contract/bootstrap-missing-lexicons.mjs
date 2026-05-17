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
  procedure("ai.gftd.agent.chat",
    { messages: objArr(), model: str(), stream: bool() },
    ["messages"],
    { response: str() },
    ["response"]),

  procedure("ai.gftd.agent.registerTools",
    { tools: objArr() },
    ["tools"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.pds.invoke",
    { did: str(), method: str(), params: obj() },
    ["did", "method"],
    { result: obj() },
    ["result"]),

  procedure("ai.gftd.pds.putProfile",
    { displayName: str(), description: str(), avatar: str() },
    [],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.pds.importRepo",
    { data: str() },
    ["data"],
    { imported: bool() },
    ["imported"]),

  procedure("ai.gftd.pds.registerSyncApp",
    { nanoid: str() },
    ["nanoid"],
    { registered: bool() },
    ["registered"]),

  procedure("ai.gftd.identity.register",
    { nanoid: str(), displayName: str() },
    ["nanoid"],
    { did: str(), registered: bool() },
    ["did", "registered"]),

  procedure("ai.gftd.governance.approveFollowRequest",
    { did: str() },
    ["did"],
    { approved: bool(), did: str() },
    ["approved", "did"]),

  procedure("ai.gftd.governance.rejectFollowRequest",
    { did: str() },
    ["did"],
    { rejected: bool(), did: str() },
    ["rejected", "did"]),

  procedure("ai.gftd.governance.approveAllFollowRequests",
    {},
    [],
    { approvedAll: bool() },
    ["approvedAll"]),

  procedure("ai.gftd.governance.registerManifest",
    { manifestJson: str() },
    ["manifestJson"],
    { registered: bool(), appId: str(), policyCount: int() },
    ["registered", "appId", "policyCount"]),

  procedure("ai.gftd.governance.registerRoleBindings",
    { appNanoid: str(), roles: objArr() },
    ["appNanoid", "roles"],
    { registered: bool(), bound: int() },
    ["registered", "bound"]),

  procedure("ai.gftd.governance.createLabel",
    { label: obj() },
    ["label"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.convo.edit",
    { convoId: str(), messageId: str(), text: str() },
    ["convoId", "messageId", "text"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.convo.send",
    { convoId: str(), text: str(), kind: str(), contentType: str() },
    ["convoId", "text"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.convo.search",
    { q: str(), convoId: str(), limit: int() },
    ["q"],
    { results: objArr() },
    ["results"]),

  procedure("ai.gftd.convo.forwardMessage",
    { convoId: str(), targetConvoId: str(), messageId: str() },
    ["convoId", "targetConvoId", "messageId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.convo.pinMessage",
    { convoId: str(), messageId: str() },
    ["convoId", "messageId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.convo.unpinMessage",
    { convoId: str(), messageId: str() },
    ["convoId", "messageId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.convo.inviteMember",
    { convoId: str(), memberDid: str() },
    ["convoId", "memberDid"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.convo.updateMemberRole",
    { convoId: str(), memberDid: str(), role: str() },
    ["convoId", "memberDid", "role"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.signal.ensureDevice",
    { deviceId: str(), deviceName: str() },
    [],
    { deviceId: str(), did: str(), provisioned: bool() },
    ["deviceId", "did", "provisioned"]),

  procedure("ai.gftd.signal.revokeDevice",
    { deviceId: str() },
    ["deviceId"],
    { deviceId: str(), revoked: bool() },
    ["deviceId", "revoked"]),

  procedure("ai.gftd.signal.renameDevice",
    { deviceId: str(), name: str() },
    ["deviceId", "name"],
    { deviceId: str(), name: str() },
    ["deviceId", "name"]),

  procedure("ai.gftd.signal.registerPrekeys",
    { identityKey: str(), signedPrekey: obj(), oneTimePrekeys: objArr(), deviceId: str() },
    ["identityKey", "signedPrekey", "oneTimePrekeys"],
    { rkey: str(), registered: bool(), otkCount: int() },
    ["rkey", "registered", "otkCount"]),

  procedure("ai.gftd.signal.replenishOtpks",
    { oneTimePrekeys: objArr(), deviceId: str() },
    ["oneTimePrekeys"],
    { replenished: bool(), count: int() },
    ["replenished", "count"]),

  procedure("ai.gftd.signal.setEncryption",
    { convoId: str(), mode: str() },
    ["convoId"],
    { convoId: str(), encryption: str() },
    ["convoId", "encryption"]),

  procedure("ai.gftd.signal.verifyIdentity",
    { did: str(), fingerprint: str() },
    ["did", "fingerprint"],
    { did: str(), verified: bool() },
    ["did", "verified"]),

  procedure("ai.gftd.signal.rotateGroupKey",
    { convoId: str() },
    ["convoId"],
    { convoId: str(), rotated: bool(), rkey: str() },
    ["convoId", "rotated", "rkey"]),

  procedure("ai.gftd.rtc.scheduleMeeting",
    { title: str(), scheduledAt: str(), participants: strArr() },
    ["title"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.rtc.joinMeeting",
    { meetingId: str() },
    ["meetingId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.rtc.admitParticipant",
    { meetingId: str(), participantDid: str() },
    ["meetingId", "participantDid"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.rtc.createBreakout",
    { meetingId: str(), name: str() },
    ["meetingId", "name"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.rtc.startRecording",
    { meetingId: str(), action: str() },
    ["meetingId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.rtc.raiseHand",
    { meetingId: str(), raised: bool() },
    ["meetingId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.rtc.openHuddle",
    { convoId: str() },
    ["convoId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.rtc.shareScreen",
    { meetingId: str(), sharing: bool() },
    ["meetingId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.stream.subscribe",
    { topics: strArr() },
    ["topics"],
    { subscriptionId: str() },
    ["subscriptionId"]),

  procedure("ai.gftd.stream.openStream",
    { topics: strArr() },
    [],
    { streamId: str() },
    ["streamId"]),

  procedure("ai.gftd.stream.closeStream",
    { streamId: str() },
    ["streamId"],
    { closed: bool() },
    ["closed"]),

  procedure("ai.gftd.apps.llm.chatCompletions",
    { messages: objArr(), model: str(), maxTokens: int() },
    ["messages"],
    { choices: objArr() },
    ["choices"]),

  procedure("ai.gftd.apps.llm.converse",
    { message: str(), model: str() },
    ["message"],
    { response: str() },
    ["response"]),

  procedure("ai.gftd.apps.llm.generateImage",
    { prompt: str(), model: str() },
    ["prompt"],
    { url: str() },
    ["url"]),

  procedure("ai.gftd.apps.celler.provisionEsim",
    { did: str(), dataPlan: str() },
    ["did"],
    { iccid: str(), status: str() },
    ["iccid", "status"]),

  procedure("ai.gftd.apps.celler.activateEsim",
    { iccid: str() },
    ["iccid"],
    { status: str(), iccid: str() },
    ["status", "iccid"]),

  procedure("ai.gftd.apps.celler.suspendEsim",
    { iccid: str() },
    ["iccid"],
    { status: str(), iccid: str() },
    ["status", "iccid"]),

  procedure("ai.gftd.apps.yoro.activity.markSeen",
    {},
    [],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.murakumo.trainExperts",
    { dataDir: str() },
    ["dataDir"],
    { status: str() },
    ["status"]),

  procedure("ai.gftd.projector.branchConvo",
    { convoId: str(), name: str() },
    ["convoId"],
    { branchConvoId: str() },
    ["branchConvoId"]),

  procedure("ai.gftd.projector.exploreThoughts",
    { convoId: str(), question: str() },
    ["convoId"],
    { reply: str(), messages: objArr() },
    ["reply", "messages"]),

  procedure("ai.gftd.projector.consistentAnswer",
    { convoId: str(), question: str() },
    ["convoId"],
    { answer: str() },
    ["answer"]),

  procedure("ai.gftd.projector.addReflection",
    { convoId: str() },
    ["convoId"],
    { rkey: str(), uri: str(), cid: str() },
    ["rkey", "uri", "cid"]),

  procedure("ai.gftd.projector.moveProject",
    { convoId: str(), targetParentUri: str() },
    ["convoId"],
    { status: str() },
    ["status"]),

  procedure("ai.gftd.projector.resolveProjectEmail",
    { email: str() },
    ["email"],
    { convoId: str() },
    ["convoId"]),

];

// ---------------------------------------------------------------------------
// Definitions — Queries
// ---------------------------------------------------------------------------

const queries = [
  query("ai.gftd.pds.query",
    { statement: str(), parameters: obj() },
    ["statement"],
    { rows: objArr() },
    ["rows"]),

  query("ai.gftd.pds.getActorProfile",
    { did: str(), handle: str() },
    [],
    { profile: obj() },
    ["profile"]),

  query("ai.gftd.pds.getProfile",
    { did: str() },
    [],
    { profile: obj() },
    ["profile"]),

  query("ai.gftd.pds.getAppPreview",
    { nanoid: str() },
    ["nanoid"],
    { app: obj() },
    ["app"]),

  query("ai.gftd.pds.getEntityGraph",
    { did: str(), depth: int() },
    ["did"],
    { nodes: objArr(), edges: objArr() },
    ["nodes", "edges"]),

  query("ai.gftd.pds.exportRepo",
    { did: str() },
    [],
    { data: str() },
    ["data"]),

  query("ai.gftd.pds.listHeartbeatApps",
    { limit: int() },
    [],
    { apps: objArr() },
    ["apps"]),

  query("ai.gftd.identity.resolve",
    { did: str(), handle: str() },
    [],
    { did: str(), handle: str() },
    ["did", "handle"]),

  query("ai.gftd.identity.list",
    { limit: int(), cursor: str() },
    [],
    { identities: objArr(), cursor: str() },
    ["identities"]),

  query("ai.gftd.identity.getEngagement",
    { did: str() },
    [],
    { engagement: obj() },
    ["engagement"]),

  query("ai.gftd.identity.pullFeed",
    { did: str(), limit: int() },
    [],
    { feed: objArr() },
    ["feed"]),

  query("ai.gftd.governance.queryLabels",
    { limit: int() },
    [],
    { labels: objArr(), cursor: str() },
    ["labels"]),

  query("ai.gftd.convo.getThread",
    { convoId: str(), messageId: str() },
    ["convoId", "messageId"],
    { thread: objArr() },
    ["thread"]),

  query("ai.gftd.convo.listMembers",
    { convoId: str() },
    ["convoId"],
    { members: objArr() },
    ["members"]),

  query("ai.gftd.convo.getUnread",
    {},
    [],
    { count: int() },
    ["count"]),

  query("ai.gftd.convo.listPresence",
    { convoId: str() },
    ["convoId"],
    { presence: objArr() },
    ["presence"]),

  query("ai.gftd.convo.listPublicConvos",
    { limit: int(), cursor: str() },
    [],
    { convos: objArr(), cursor: str() },
    ["convos"]),

  query("ai.gftd.convo.getProfile",
    {},
    [],
    { profile: obj() },
    ["profile"]),

  query("ai.gftd.convo.fetchBlocks",
    { convoId: str() },
    [],
    { blocks: objArr() },
    ["blocks"]),

  query("ai.gftd.signal.listDevices",
    {},
    [],
    { devices: objArr() },
    ["devices"]),

  query("ai.gftd.signal.getIdentityFingerprint",
    { did: str() },
    [],
    { did: str(), fingerprint: str() },
    ["did", "fingerprint"]),

  query("ai.gftd.signal.getPrekeyBundle",
    { did: str() },
    ["did"],
    { bundle: obj() },
    ["bundle"]),

  query("ai.gftd.signal.getPrekeyBundles",
    { did: str() },
    ["did"],
    { bundles: objArr() },
    ["bundles"]),


  query("ai.gftd.stream.readFrames",
    { streamId: str(), limit: int() },
    ["streamId"],
    { frames: objArr() },
    ["frames"]),

  query("ai.gftd.apps.celler.getEsimProfile",
    {},
    [],
    { profiles: objArr() },
    ["profiles"]),

  query("ai.gftd.apps.yoro.activity.listActivities",
    { limit: int(), cursor: str(), objectTypes: str(), actorDid: str() },
    [],
    { events: objArr(), cursor: str() },
    ["events"]),

  query("ai.gftd.apps.yoro.activity.getActivityTrace",
    { objectType: str(), objectId: str() },
    ["objectType", "objectId"],
    { trace: objArr() },
    ["trace"]),

  query("ai.gftd.projector.loadProjectChat",
    { convoId: str() },
    ["convoId"],
    { convoId: str(), messages: objArr(), members: objArr() },
    ["convoId", "messages", "members"]),

  query("ai.gftd.projector.listProjectTree",
    { convoId: str(), maxDepth: int() },
    ["convoId"],
    { tree: objArr() },
    ["tree"]),

  query("ai.gftd.projector.listBranches",
    { convoId: str(), offset: int(), limit: int() },
    ["convoId"],
    { branches: objArr() },
    ["branches"]),

  query("ai.gftd.projector.listReflections",
    { convoId: str(), offset: int(), limit: int() },
    ["convoId"],
    { reflections: objArr() },
    ["reflections"]),

  query("ai.gftd.projector.getProjectUnreadCounts",
    { convoId: str() },
    [],
    { counts: objArr() },
    ["counts"]),

  query("ai.gftd.projector.listProjectNotifications",
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
