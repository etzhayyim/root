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
    id: "com.etzhayyim.agent.actorCard",
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
    id: "com.etzhayyim.agent.actorCapability",
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
    id: "com.etzhayyim.agent.agentTools",
    props: {
      tools: { type: "array", items: { type: "unknown" } },
      createdAt: { type: "string" },
    },
    required: ["tools", "createdAt"],
  },
  {
    id: "com.etzhayyim.agent.governanceRule",
    props: {
      name: { type: "string" },
      rules: { type: "unknown" },
    },
    required: ["name", "rules"],
  },
  {
    id: "com.etzhayyim.agent.roleBinding",
    props: {
      role: { type: "string" },
      did: { type: "string" },
      description: { type: "string" },
    },
    required: ["role", "did"],
  },
  {
    id: "com.etzhayyim.apps.yoro.activitySeen",
    props: {
      seenAt: { type: "string" },
    },
    required: ["seenAt"],
  },
  {
    id: "com.etzhayyim.apps.yoro.projectEntity",
    props: {
      projectId: { type: "string" },
      entityType: { type: "string" },
      entityId: { type: "string" },
    },
    required: ["projectId", "entityType", "entityId"],
  },
  {
    id: "com.etzhayyim.apps.yoro.shinkaEvolution",
    props: {
      nanoid: { type: "string" },
      evolutionData: { type: "unknown" },
    },
    required: ["nanoid", "evolutionData"],
  },
  {
    id: "com.etzhayyim.apps.yoro.shinkaKnowledge",
    props: {
      nanoid: { type: "string" },
      knowledgeData: { type: "unknown" },
    },
    required: ["nanoid", "knowledgeData"],
  },
  {
    id: "com.etzhayyim.auth.AgentKey",
    props: {
      keyId: { type: "string" },
      publicKey: { type: "string" },
      createdAt: { type: "string" },
    },
    required: ["keyId", "publicKey", "createdAt"],
  },
  {
    id: "com.etzhayyim.convo.convo",
    props: {
      name: { type: "string" },
      kind: { type: "string" },
      createdBy: { type: "string" },
      createdAt: { type: "string" },
    },
    required: ["name", "createdBy", "createdAt"],
  },
  {
    id: "com.etzhayyim.convo.message",
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
    id: "com.etzhayyim.convo.reaction",
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
    id: "com.etzhayyim.convo.readReceipt",
    props: {
      convoId: { type: "string" },
      readAt: { type: "string" },
    },
    required: ["convoId", "readAt"],
  },
  {
    id: "com.etzhayyim.convo.membership",
    props: {
      convoId: { type: "string" },
      action: { type: "string" },
      memberDid: { type: "string" },
    },
    required: ["convoId", "action", "memberDid"],
  },
  {
    id: "com.etzhayyim.convo.convoUpdate",
    props: {
      convoId: { type: "string" },
      updatedAt: { type: "string" },
    },
    required: ["convoId", "updatedAt"],
  },
  {
    id: "com.etzhayyim.convo.invite",
    props: {
      convoId: { type: "string" },
      invitedDid: { type: "string" },
      invitedAt: { type: "string" },
    },
    required: ["convoId", "invitedDid", "invitedAt"],
  },
  {
    id: "com.etzhayyim.convo.roleUpdate",
    props: {
      convoId: { type: "string" },
      memberDid: { type: "string" },
      role: { type: "string" },
      updatedAt: { type: "string" },
    },
    required: ["convoId", "memberDid", "role", "updatedAt"],
  },
  {
    id: "com.etzhayyim.convo.presence",
    props: {
      status: { type: "string" },
      updatedAt: { type: "string" },
    },
    required: ["status", "updatedAt"],
  },
  {
    id: "com.etzhayyim.convo.profile",
    props: {
      displayName: { type: "string" },
      description: { type: "string" },
      avatar: { type: "string" },
    },
    required: [],
  },
  {
    id: "com.etzhayyim.convo.pin",
    props: {
      convoId: { type: "string" },
      messageId: { type: "string" },
      pinnedAt: { type: "string" },
    },
    required: ["convoId", "messageId", "pinnedAt"],
  },
  {
    id: "com.etzhayyim.convo.forward",
    props: {
      sourceConvoId: { type: "string" },
      targetConvoId: { type: "string" },
      messageId: { type: "string" },
      forwardedAt: { type: "string" },
    },
    required: ["sourceConvoId", "targetConvoId", "messageId", "forwardedAt"],
  },
  {
    id: "com.etzhayyim.convo.member",
    props: {
      convoId: { type: "string" },
      memberDid: { type: "string" },
      role: { type: "string" },
    },
    required: ["convoId", "memberDid"],
  },
  {
    id: "com.etzhayyim.projector",
    props: {
      projectId: { type: "string" },
      name: { type: "string" },
      convoId: { type: "string" },
      status: { type: "string" },
    },
    required: ["projectId", "name", "convoId"],
  },
  {
    id: "com.etzhayyim.projector.branch",
    props: {
      sourceConvoId: { type: "string" },
      branchConvoId: { type: "string" },
      branchPointRkey: { type: "string" },
    },
    required: ["sourceConvoId", "branchConvoId"],
  },
  {
    id: "com.etzhayyim.projector.reflection",
    props: {
      convoId: { type: "string" },
      content: { type: "string" },
    },
    required: ["convoId"],
  },
  {
    id: "com.etzhayyim.projectorTask",
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
    id: "com.etzhayyim.projectorUpdate",
    props: {
      convoId: { type: "string" },
      updateType: { type: "string" },
    },
    required: ["convoId", "updateType"],
  },
  {
    id: "com.etzhayyim.rtc.meeting",
    props: {
      title: { type: "string" },
      scheduledAt: { type: "string" },
      status: { type: "string" },
    },
    required: ["title", "status"],
  },
  {
    id: "com.etzhayyim.rtc.meetingJoin",
    props: {
      meetingId: { type: "string" },
      participantDid: { type: "string" },
    },
    required: ["meetingId", "participantDid"],
  },
  {
    id: "com.etzhayyim.rtc.meetingAdmit",
    props: {
      meetingId: { type: "string" },
      participantDid: { type: "string" },
    },
    required: ["meetingId", "participantDid"],
  },
  {
    id: "com.etzhayyim.rtc.breakout",
    props: {
      meetingId: { type: "string" },
      name: { type: "string" },
    },
    required: ["meetingId", "name"],
  },
  {
    id: "com.etzhayyim.rtc.recording",
    props: {
      meetingId: { type: "string" },
      action: { type: "string" },
    },
    required: ["meetingId", "action"],
  },
  {
    id: "com.etzhayyim.rtc.hand",
    props: {
      meetingId: { type: "string" },
      raised: { type: "boolean" },
    },
    required: ["meetingId", "raised"],
  },
  {
    id: "com.etzhayyim.rtc.huddle",
    props: {
      convoId: { type: "string" },
    },
    required: ["convoId"],
  },
  {
    id: "com.etzhayyim.rtc.screenShare",
    props: {
      meetingId: { type: "string" },
      sharing: { type: "boolean" },
    },
    required: ["meetingId", "sharing"],
  },
  {
    id: "com.etzhayyim.rtc.pushSubscription",
    props: {
      endpoint: { type: "string" },
      keys: { type: "unknown" },
    },
    required: ["endpoint", "keys"],
  },
  {
    id: "com.etzhayyim.signal.prekeys",
    props: {
      identityKey: { type: "string" },
      signedPrekey: { type: "unknown" },
      oneTimePrekeys: { type: "array", items: { type: "unknown" } },
    },
    required: ["identityKey", "signedPrekey", "oneTimePrekeys"],
  },
  {
    id: "com.etzhayyim.signal.otpks",
    props: {
      oneTimePrekeys: { type: "array", items: { type: "unknown" } },
    },
    required: ["oneTimePrekeys"],
  },
  {
    id: "com.etzhayyim.signal.groupKeyRotation",
    props: {
      convoId: { type: "string" },
      rotatedAt: { type: "string" },
    },
    required: ["convoId", "rotatedAt"],
  },
  {
    id: "com.etzhayyim.wproto.did",
    props: {
      did: { type: "string" },
      document: { type: "unknown" },
    },
    required: ["did", "document"],
  },
  {
    id: "com.etzhayyim.wproto.label",
    props: {
      label: { type: "string" },
      val: { type: "string" },
    },
    required: ["label", "val"],
  },
  {
    id: "com.etzhayyim.pds.profileIncomplete",
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
  { alias: "com.etzhayyim.convo.archiveConvo", source: "com.etzhayyim.convo.convo.archiveConvo" },
  { alias: "com.etzhayyim.convo.createConvo", source: "com.etzhayyim.convo.convo.createConvo" },
  { alias: "com.etzhayyim.convo.joinConvo", source: "com.etzhayyim.convo.convo.joinConvo" },
  { alias: "com.etzhayyim.convo.sendTyping", source: "com.etzhayyim.convo.convo.sendTyping" },
  { alias: "com.etzhayyim.convo.setProfile", source: "com.etzhayyim.convo.convo.setProfile" },
  { alias: "com.etzhayyim.convo.updateConvo", source: "com.etzhayyim.convo.convo.updateConvo" },
  { alias: "com.etzhayyim.convo.updatePresence", source: "com.etzhayyim.convo.convo.updatePresence" },
  { alias: "com.etzhayyim.convo.setEncryption", source: "com.etzhayyim.convo.convo.setConvoEncryption" },
  { alias: "com.etzhayyim.governance.checkAccess", source: "com.etzhayyim.governance.governance.checkAccess" },
  { alias: "com.etzhayyim.governance.getPolicy", source: "com.etzhayyim.governance.governance.getPolicy" },
  { alias: "com.etzhayyim.governance.registerMethodPolicy", source: "com.etzhayyim.governance.governance.registerMethodPolicy" },
  { alias: "com.etzhayyim.governance.registerPolicy", source: "com.etzhayyim.governance.governance.registerPolicy" },
  { alias: "com.etzhayyim.governance.resolveActorVisibility", source: "com.etzhayyim.governance.governance.resolveActorVisibility" },
  { alias: "com.etzhayyim.governance.setActorSensitivity", source: "com.etzhayyim.governance.governance.setActorSensitivity" },
  { alias: "com.etzhayyim.projector.addConvoMember", source: "com.etzhayyim.projector.projector.addConvoMember" },
  { alias: "com.etzhayyim.projector.addConvoTask", source: "com.etzhayyim.projector.projector.addConvoTask" },
  { alias: "com.etzhayyim.projector.archiveProjectConvo", source: "com.etzhayyim.projector.projector.archiveProjectConvo" },
  { alias: "com.etzhayyim.projector.completeConvoTask", source: "com.etzhayyim.projector.projector.completeConvoTask" },
  { alias: "com.etzhayyim.projector.getConvoProjectStatus", source: "com.etzhayyim.projector.projector.getConvoProjectStatus" },
  { alias: "com.etzhayyim.projector.getProjectConvo", source: "com.etzhayyim.projector.projector.getProjectConvo" },
  { alias: "com.etzhayyim.projector.listConvoTasks", source: "com.etzhayyim.projector.projector.listConvoTasks" },
  { alias: "com.etzhayyim.projector.listProjectConvos", source: "com.etzhayyim.projector.projector.listProjectConvos" },
  { alias: "com.etzhayyim.projector.newProjectConvo", source: "com.etzhayyim.projector.projector.newProjectConvo" },
  { alias: "com.etzhayyim.projector.sendProjectMessage", source: "com.etzhayyim.projector.projector.sendProjectMessage" },
  { alias: "com.etzhayyim.projector.updateProjectConvo", source: "com.etzhayyim.projector.projector.updateProjectConvo" },
  { alias: "com.etzhayyim.rtc.getVAPIDPublicKey", source: "com.etzhayyim.rtc.rtc.getVapidPublicKey" },
  { alias: "com.etzhayyim.rtc.hangupCall", source: "com.etzhayyim.rtc.rtc.hangupCall" },
  { alias: "com.etzhayyim.rtc.sendCallAnswer", source: "com.etzhayyim.rtc.rtc.sendCallAnswer" },
  { alias: "com.etzhayyim.rtc.sendCallICE", source: "com.etzhayyim.rtc.rtc.sendCallIce" },
  { alias: "com.etzhayyim.rtc.sendCallOffer", source: "com.etzhayyim.rtc.rtc.sendCallOffer" },
  { alias: "com.etzhayyim.rtc.subscribePush", source: "com.etzhayyim.rtc.rtc.subscribePush" },
  { alias: "com.etzhayyim.rtc.unsubscribePush", source: "com.etzhayyim.rtc.rtc.unsubscribePush" },
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
