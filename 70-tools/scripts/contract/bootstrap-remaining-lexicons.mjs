#!/usr/bin/env node
/**
 * bootstrap-remaining-lexicons.mjs
 *
 * Creates all missing Lexicon JSON files for:
 *   1. Record collection types (type: "record")
 *   2. 4-segment handler alias NSIDs (copy from existing 5-segment, change id)
 */
import { mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";

const ROOT = new URL("../../../00-contracts/lexicons", import.meta.url).pathname;

function nsidToPath(nsid) {
  const parts = nsid.split(".");
  const fileName = parts.pop() + ".json";
  return join(ROOT, ...parts, fileName);
}

function writeIfMissing(path, data) {
  if (existsSync(path)) {
    console.log(`  SKIP (exists): ${path}`);
    return false;
  }
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(data, null, 2) + "\n");
  console.log(`  CREATED: ${path}`);
  return true;
}

// ---------------------------------------------------------------------------
// Category 1: Record collection types
// ---------------------------------------------------------------------------
const records = [
  {
    id: "app.etzhayyim.agent.actorCard",
    props: {
      nanoid: { type: "string" },
      name: { type: "string" },
      description: { type: "string" },
      protocols: { type: "string" },
      toolsJson: { type: "string" },
      createdAt: { type: "string" },
    },
    required: ["nanoid", "name", "createdAt"],
  },
  {
    id: "app.etzhayyim.agent.actorCapability",
    props: {
      id: { type: "string" },
      name: { type: "string" },
      description: { type: "string" },
      status: { type: "string" },
      phase: { type: "string" },
      tags: { type: "string" },
      createdAt: { type: "string" },
    },
    required: ["id", "name", "createdAt"],
  },
  {
    id: "app.etzhayyim.agent.agentTools",
    props: {
      tools: { type: "array", items: { type: "unknown" } },
      createdAt: { type: "string" },
    },
    required: ["tools", "createdAt"],
  },
  {
    id: "app.etzhayyim.agent.governanceRule",
    props: {
      name: { type: "string" },
      rules: { type: "unknown" },
    },
    required: ["name", "rules"],
  },
  {
    id: "app.etzhayyim.agent.roleBinding",
    props: {
      role: { type: "string" },
      did: { type: "string" },
      description: { type: "string" },
    },
    required: ["role", "did"],
  },
  {
    id: "app.etzhayyim.apps.yoro.activitySeen",
    props: {
      seenAt: { type: "string" },
    },
    required: ["seenAt"],
  },
  {
    id: "app.etzhayyim.apps.yoro.projectEntity",
    props: {
      projectId: { type: "string" },
      entityType: { type: "string" },
      entityId: { type: "string" },
    },
    required: ["projectId", "entityType", "entityId"],
  },
  {
    id: "app.etzhayyim.apps.yoro.shinkaEvolution",
    props: {
      nanoid: { type: "string" },
      evolutionData: { type: "unknown" },
    },
    required: ["nanoid", "evolutionData"],
  },
  {
    id: "app.etzhayyim.apps.yoro.shinkaKnowledge",
    props: {
      nanoid: { type: "string" },
      knowledgeData: { type: "unknown" },
    },
    required: ["nanoid", "knowledgeData"],
  },
  {
    id: "app.etzhayyim.auth.AgentKey",
    props: {
      keyId: { type: "string" },
      publicKey: { type: "string" },
      createdAt: { type: "string" },
    },
    required: ["keyId", "publicKey", "createdAt"],
  },
  {
    id: "app.etzhayyim.convo.convo",
    props: {
      name: { type: "string" },
      kind: { type: "string" },
      createdBy: { type: "string" },
      createdAt: { type: "string" },
    },
    required: ["name", "createdBy", "createdAt"],
  },
  {
    id: "app.etzhayyim.convo.message",
    props: {
      convoId: { type: "string" },
      text: { type: "string" },
      sender: { type: "string" },
      sentAt: { type: "string" },
      kind: { type: "string" },
      contentType: { type: "string" },
    },
    required: ["convoId", "sender", "sentAt"],
  },
  {
    id: "app.etzhayyim.convo.reaction",
    props: {
      convoId: { type: "string" },
      messageId: { type: "string" },
      emoji: { type: "string" },
      reactor: { type: "string" },
      createdAt: { type: "string" },
    },
    required: ["convoId", "messageId", "emoji", "reactor", "createdAt"],
  },
  {
    id: "app.etzhayyim.convo.readReceipt",
    props: {
      convoId: { type: "string" },
      readAt: { type: "string" },
    },
    required: ["convoId", "readAt"],
  },
  {
    id: "app.etzhayyim.convo.membership",
    props: {
      convoId: { type: "string" },
      action: { type: "string" },
      memberDid: { type: "string" },
    },
    required: ["convoId", "action", "memberDid"],
  },
  {
    id: "app.etzhayyim.convo.convoUpdate",
    props: {
      convoId: { type: "string" },
      updatedAt: { type: "string" },
    },
    required: ["convoId", "updatedAt"],
  },
  {
    id: "app.etzhayyim.convo.invite",
    props: {
      convoId: { type: "string" },
      invitedDid: { type: "string" },
      invitedAt: { type: "string" },
    },
    required: ["convoId", "invitedDid", "invitedAt"],
  },
  {
    id: "app.etzhayyim.convo.roleUpdate",
    props: {
      convoId: { type: "string" },
      memberDid: { type: "string" },
      role: { type: "string" },
      updatedAt: { type: "string" },
    },
    required: ["convoId", "memberDid", "role", "updatedAt"],
  },
  {
    id: "app.etzhayyim.convo.presence",
    props: {
      status: { type: "string" },
      updatedAt: { type: "string" },
    },
    required: ["status", "updatedAt"],
  },
  {
    id: "app.etzhayyim.convo.profile",
    props: {
      displayName: { type: "string" },
      description: { type: "string" },
      avatar: { type: "string" },
    },
    required: [],
  },
  {
    id: "app.etzhayyim.convo.pin",
    props: {
      convoId: { type: "string" },
      messageId: { type: "string" },
      pinnedAt: { type: "string" },
    },
    required: ["convoId", "messageId", "pinnedAt"],
  },
  {
    id: "app.etzhayyim.convo.forward",
    props: {
      sourceConvoId: { type: "string" },
      targetConvoId: { type: "string" },
      messageId: { type: "string" },
      forwardedAt: { type: "string" },
    },
    required: ["sourceConvoId", "targetConvoId", "messageId", "forwardedAt"],
  },
  {
    id: "app.etzhayyim.convo.member",
    props: {
      convoId: { type: "string" },
      memberDid: { type: "string" },
      role: { type: "string" },
    },
    required: ["convoId", "memberDid"],
  },
  {
    id: "app.etzhayyim.projector",
    props: {
      projectId: { type: "string" },
      name: { type: "string" },
      convoId: { type: "string" },
      status: { type: "string" },
    },
    required: ["projectId", "name", "convoId"],
  },
  {
    id: "app.etzhayyim.projector.branch",
    props: {
      sourceConvoId: { type: "string" },
      branchConvoId: { type: "string" },
      branchPointRkey: { type: "string" },
    },
    required: ["sourceConvoId", "branchConvoId"],
  },
  {
    id: "app.etzhayyim.projector.reflection",
    props: {
      convoId: { type: "string" },
      content: { type: "string" },
    },
    required: ["convoId"],
  },
  {
    id: "app.etzhayyim.projectorTask",
    props: {
      convoId: { type: "string" },
      title: { type: "string" },
      status: { type: "string" },
      priority: { type: "string" },
      assigneeDid: { type: "string" },
    },
    required: ["convoId", "title", "status"],
  },
  {
    id: "app.etzhayyim.projectorUpdate",
    props: {
      convoId: { type: "string" },
      updateType: { type: "string" },
    },
    required: ["convoId", "updateType"],
  },
  {
    id: "app.etzhayyim.rtc.meeting",
    props: {
      title: { type: "string" },
      scheduledAt: { type: "string" },
      status: { type: "string" },
    },
    required: ["title", "status"],
  },
  {
    id: "app.etzhayyim.rtc.meetingJoin",
    props: {
      meetingId: { type: "string" },
      participantDid: { type: "string" },
    },
    required: ["meetingId", "participantDid"],
  },
  {
    id: "app.etzhayyim.rtc.meetingAdmit",
    props: {
      meetingId: { type: "string" },
      participantDid: { type: "string" },
    },
    required: ["meetingId", "participantDid"],
  },
  {
    id: "app.etzhayyim.rtc.breakout",
    props: {
      meetingId: { type: "string" },
      name: { type: "string" },
    },
    required: ["meetingId", "name"],
  },
  {
    id: "app.etzhayyim.rtc.recording",
    props: {
      meetingId: { type: "string" },
      action: { type: "string" },
    },
    required: ["meetingId", "action"],
  },
  {
    id: "app.etzhayyim.rtc.hand",
    props: {
      meetingId: { type: "string" },
      raised: { type: "boolean" },
    },
    required: ["meetingId", "raised"],
  },
  {
    id: "app.etzhayyim.rtc.huddle",
    props: {
      convoId: { type: "string" },
    },
    required: ["convoId"],
  },
  {
    id: "app.etzhayyim.rtc.screenShare",
    props: {
      meetingId: { type: "string" },
      sharing: { type: "boolean" },
    },
    required: ["meetingId", "sharing"],
  },
  {
    id: "app.etzhayyim.rtc.pushSubscription",
    props: {
      endpoint: { type: "string" },
      keys: { type: "unknown" },
    },
    required: ["endpoint", "keys"],
  },
  {
    id: "app.etzhayyim.signal.prekeys",
    props: {
      identityKey: { type: "string" },
      signedPrekey: { type: "unknown" },
      oneTimePrekeys: { type: "array", items: { type: "unknown" } },
    },
    required: ["identityKey", "signedPrekey", "oneTimePrekeys"],
  },
  {
    id: "app.etzhayyim.signal.otpks",
    props: {
      oneTimePrekeys: { type: "array", items: { type: "unknown" } },
    },
    required: ["oneTimePrekeys"],
  },
  {
    id: "app.etzhayyim.signal.groupKeyRotation",
    props: {
      convoId: { type: "string" },
      rotatedAt: { type: "string" },
    },
    required: ["convoId", "rotatedAt"],
  },
  {
    id: "app.etzhayyim.wproto.did",
    props: {
      did: { type: "string" },
      document: { type: "unknown" },
    },
    required: ["did", "document"],
  },
  {
    id: "app.etzhayyim.wproto.label",
    props: {
      label: { type: "string" },
      val: { type: "string" },
    },
    required: ["label", "val"],
  },
  {
    id: "app.etzhayyim.pds.profileIncomplete",
    props: {
      did: { type: "string" },
      reason: { type: "string" },
    },
    required: ["did", "reason"],
  },
];

function buildRecordLexicon(r) {
  return {
    lexicon: 1,
    id: r.id,
    defs: {
      main: {
        type: "record",
        record: {
          type: "object",
          properties: r.props,
          required: r.required,
        },
      },
    },
  };
}

// ---------------------------------------------------------------------------
// Category 2: 4-segment handler alias NSIDs
// ---------------------------------------------------------------------------
const aliases = [
  { alias: "app.etzhayyim.convo.archiveConvo", source: "app.etzhayyim.convo.convo.archiveConvo" },
  { alias: "app.etzhayyim.convo.createConvo", source: "app.etzhayyim.convo.convo.createConvo" },
  { alias: "app.etzhayyim.convo.joinConvo", source: "app.etzhayyim.convo.convo.joinConvo" },
  { alias: "app.etzhayyim.convo.sendTyping", source: "app.etzhayyim.convo.convo.sendTyping" },
  { alias: "app.etzhayyim.convo.setProfile", source: "app.etzhayyim.convo.convo.setProfile" },
  { alias: "app.etzhayyim.convo.updateConvo", source: "app.etzhayyim.convo.convo.updateConvo" },
  { alias: "app.etzhayyim.convo.updatePresence", source: "app.etzhayyim.convo.convo.updatePresence" },
  { alias: "app.etzhayyim.convo.setEncryption", source: "app.etzhayyim.convo.convo.setConvoEncryption" },
  { alias: "app.etzhayyim.governance.checkAccess", source: "app.etzhayyim.governance.governance.checkAccess" },
  { alias: "app.etzhayyim.governance.getPolicy", source: "app.etzhayyim.governance.governance.getPolicy" },
  { alias: "app.etzhayyim.governance.registerMethodPolicy", source: "app.etzhayyim.governance.governance.registerMethodPolicy" },
  { alias: "app.etzhayyim.governance.registerPolicy", source: "app.etzhayyim.governance.governance.registerPolicy" },
  { alias: "app.etzhayyim.governance.resolveActorVisibility", source: "app.etzhayyim.governance.governance.resolveActorVisibility" },
  { alias: "app.etzhayyim.governance.setActorSensitivity", source: "app.etzhayyim.governance.governance.setActorSensitivity" },
  { alias: "app.etzhayyim.projector.addConvoMember", source: "app.etzhayyim.projector.projector.addConvoMember" },
  { alias: "app.etzhayyim.projector.addConvoTask", source: "app.etzhayyim.projector.projector.addConvoTask" },
  { alias: "app.etzhayyim.projector.archiveProjectConvo", source: "app.etzhayyim.projector.projector.archiveProjectConvo" },
  { alias: "app.etzhayyim.projector.completeConvoTask", source: "app.etzhayyim.projector.projector.completeConvoTask" },
  { alias: "app.etzhayyim.projector.getConvoProjectStatus", source: "app.etzhayyim.projector.projector.getConvoProjectStatus" },
  { alias: "app.etzhayyim.projector.getProjectConvo", source: "app.etzhayyim.projector.projector.getProjectConvo" },
  { alias: "app.etzhayyim.projector.listConvoTasks", source: "app.etzhayyim.projector.projector.listConvoTasks" },
  { alias: "app.etzhayyim.projector.listProjectConvos", source: "app.etzhayyim.projector.projector.listProjectConvos" },
  { alias: "app.etzhayyim.projector.newProjectConvo", source: "app.etzhayyim.projector.projector.newProjectConvo" },
  { alias: "app.etzhayyim.projector.sendProjectMessage", source: "app.etzhayyim.projector.projector.sendProjectMessage" },
  { alias: "app.etzhayyim.projector.updateProjectConvo", source: "app.etzhayyim.projector.projector.updateProjectConvo" },
  { alias: "app.etzhayyim.rtc.getVAPIDPublicKey", source: "app.etzhayyim.rtc.rtc.getVapidPublicKey" },
  { alias: "app.etzhayyim.rtc.hangupCall", source: "app.etzhayyim.rtc.rtc.hangupCall" },
  { alias: "app.etzhayyim.rtc.sendCallAnswer", source: "app.etzhayyim.rtc.rtc.sendCallAnswer" },
  { alias: "app.etzhayyim.rtc.sendCallICE", source: "app.etzhayyim.rtc.rtc.sendCallIce" },
  { alias: "app.etzhayyim.rtc.sendCallOffer", source: "app.etzhayyim.rtc.rtc.sendCallOffer" },
  { alias: "app.etzhayyim.rtc.subscribePush", source: "app.etzhayyim.rtc.rtc.subscribePush" },
  { alias: "app.etzhayyim.rtc.unsubscribePush", source: "app.etzhayyim.rtc.rtc.unsubscribePush" },
];

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------
let created = 0;
let skipped = 0;
let errors = 0;

console.log("=== Category 1: Record collection types ===\n");
for (const r of records) {
  const path = nsidToPath(r.id);
  if (writeIfMissing(path, buildRecordLexicon(r))) {
    created++;
  } else {
    skipped++;
  }
}

console.log("\n=== Category 2: 4-segment handler alias NSIDs ===\n");
for (const { alias, source } of aliases) {
  const sourcePath = nsidToPath(source);
  const aliasPath = nsidToPath(alias);

  if (!existsSync(sourcePath)) {
    console.error(`  ERROR: source missing: ${sourcePath}`);
    errors++;
    continue;
  }

  const sourceData = JSON.parse(readFileSync(sourcePath, "utf-8"));
  sourceData.id = alias;
  if (writeIfMissing(aliasPath, sourceData)) {
    created++;
  } else {
    skipped++;
  }
}

console.log(`\n=== Summary ===`);
console.log(`  Created: ${created}`);
console.log(`  Skipped: ${skipped}`);
console.log(`  Errors:  ${errors}`);
console.log(`  Total:   ${created + skipped + errors}`);
