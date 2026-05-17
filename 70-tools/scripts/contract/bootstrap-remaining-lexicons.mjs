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
    id: "ai.gftd.agent.actorCard",
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
    id: "ai.gftd.agent.actorCapability",
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
    id: "ai.gftd.agent.agentTools",
    props: {
      tools: { type: "array", items: { type: "unknown" } },
      createdAt: { type: "string" },
    },
    required: ["tools", "createdAt"],
  },
  {
    id: "ai.gftd.agent.governanceRule",
    props: {
      name: { type: "string" },
      rules: { type: "unknown" },
    },
    required: ["name", "rules"],
  },
  {
    id: "ai.gftd.agent.roleBinding",
    props: {
      role: { type: "string" },
      did: { type: "string" },
      description: { type: "string" },
    },
    required: ["role", "did"],
  },
  {
    id: "ai.gftd.apps.yoro.activitySeen",
    props: {
      seenAt: { type: "string" },
    },
    required: ["seenAt"],
  },
  {
    id: "ai.gftd.apps.yoro.projectEntity",
    props: {
      projectId: { type: "string" },
      entityType: { type: "string" },
      entityId: { type: "string" },
    },
    required: ["projectId", "entityType", "entityId"],
  },
  {
    id: "ai.gftd.apps.yoro.shinkaEvolution",
    props: {
      nanoid: { type: "string" },
      evolutionData: { type: "unknown" },
    },
    required: ["nanoid", "evolutionData"],
  },
  {
    id: "ai.gftd.apps.yoro.shinkaKnowledge",
    props: {
      nanoid: { type: "string" },
      knowledgeData: { type: "unknown" },
    },
    required: ["nanoid", "knowledgeData"],
  },
  {
    id: "ai.gftd.auth.AgentKey",
    props: {
      keyId: { type: "string" },
      publicKey: { type: "string" },
      createdAt: { type: "string" },
    },
    required: ["keyId", "publicKey", "createdAt"],
  },
  {
    id: "ai.gftd.convo.convo",
    props: {
      name: { type: "string" },
      kind: { type: "string" },
      createdBy: { type: "string" },
      createdAt: { type: "string" },
    },
    required: ["name", "createdBy", "createdAt"],
  },
  {
    id: "ai.gftd.convo.message",
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
    id: "ai.gftd.convo.reaction",
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
    id: "ai.gftd.convo.readReceipt",
    props: {
      convoId: { type: "string" },
      readAt: { type: "string" },
    },
    required: ["convoId", "readAt"],
  },
  {
    id: "ai.gftd.convo.membership",
    props: {
      convoId: { type: "string" },
      action: { type: "string" },
      memberDid: { type: "string" },
    },
    required: ["convoId", "action", "memberDid"],
  },
  {
    id: "ai.gftd.convo.convoUpdate",
    props: {
      convoId: { type: "string" },
      updatedAt: { type: "string" },
    },
    required: ["convoId", "updatedAt"],
  },
  {
    id: "ai.gftd.convo.invite",
    props: {
      convoId: { type: "string" },
      invitedDid: { type: "string" },
      invitedAt: { type: "string" },
    },
    required: ["convoId", "invitedDid", "invitedAt"],
  },
  {
    id: "ai.gftd.convo.roleUpdate",
    props: {
      convoId: { type: "string" },
      memberDid: { type: "string" },
      role: { type: "string" },
      updatedAt: { type: "string" },
    },
    required: ["convoId", "memberDid", "role", "updatedAt"],
  },
  {
    id: "ai.gftd.convo.presence",
    props: {
      status: { type: "string" },
      updatedAt: { type: "string" },
    },
    required: ["status", "updatedAt"],
  },
  {
    id: "ai.gftd.convo.profile",
    props: {
      displayName: { type: "string" },
      description: { type: "string" },
      avatar: { type: "string" },
    },
    required: [],
  },
  {
    id: "ai.gftd.convo.pin",
    props: {
      convoId: { type: "string" },
      messageId: { type: "string" },
      pinnedAt: { type: "string" },
    },
    required: ["convoId", "messageId", "pinnedAt"],
  },
  {
    id: "ai.gftd.convo.forward",
    props: {
      sourceConvoId: { type: "string" },
      targetConvoId: { type: "string" },
      messageId: { type: "string" },
      forwardedAt: { type: "string" },
    },
    required: ["sourceConvoId", "targetConvoId", "messageId", "forwardedAt"],
  },
  {
    id: "ai.gftd.convo.member",
    props: {
      convoId: { type: "string" },
      memberDid: { type: "string" },
      role: { type: "string" },
    },
    required: ["convoId", "memberDid"],
  },
  {
    id: "ai.gftd.projector",
    props: {
      projectId: { type: "string" },
      name: { type: "string" },
      convoId: { type: "string" },
      status: { type: "string" },
    },
    required: ["projectId", "name", "convoId"],
  },
  {
    id: "ai.gftd.projector.branch",
    props: {
      sourceConvoId: { type: "string" },
      branchConvoId: { type: "string" },
      branchPointRkey: { type: "string" },
    },
    required: ["sourceConvoId", "branchConvoId"],
  },
  {
    id: "ai.gftd.projector.reflection",
    props: {
      convoId: { type: "string" },
      content: { type: "string" },
    },
    required: ["convoId"],
  },
  {
    id: "ai.gftd.projectorTask",
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
    id: "ai.gftd.projectorUpdate",
    props: {
      convoId: { type: "string" },
      updateType: { type: "string" },
    },
    required: ["convoId", "updateType"],
  },
  {
    id: "ai.gftd.rtc.meeting",
    props: {
      title: { type: "string" },
      scheduledAt: { type: "string" },
      status: { type: "string" },
    },
    required: ["title", "status"],
  },
  {
    id: "ai.gftd.rtc.meetingJoin",
    props: {
      meetingId: { type: "string" },
      participantDid: { type: "string" },
    },
    required: ["meetingId", "participantDid"],
  },
  {
    id: "ai.gftd.rtc.meetingAdmit",
    props: {
      meetingId: { type: "string" },
      participantDid: { type: "string" },
    },
    required: ["meetingId", "participantDid"],
  },
  {
    id: "ai.gftd.rtc.breakout",
    props: {
      meetingId: { type: "string" },
      name: { type: "string" },
    },
    required: ["meetingId", "name"],
  },
  {
    id: "ai.gftd.rtc.recording",
    props: {
      meetingId: { type: "string" },
      action: { type: "string" },
    },
    required: ["meetingId", "action"],
  },
  {
    id: "ai.gftd.rtc.hand",
    props: {
      meetingId: { type: "string" },
      raised: { type: "boolean" },
    },
    required: ["meetingId", "raised"],
  },
  {
    id: "ai.gftd.rtc.huddle",
    props: {
      convoId: { type: "string" },
    },
    required: ["convoId"],
  },
  {
    id: "ai.gftd.rtc.screenShare",
    props: {
      meetingId: { type: "string" },
      sharing: { type: "boolean" },
    },
    required: ["meetingId", "sharing"],
  },
  {
    id: "ai.gftd.rtc.pushSubscription",
    props: {
      endpoint: { type: "string" },
      keys: { type: "unknown" },
    },
    required: ["endpoint", "keys"],
  },
  {
    id: "ai.gftd.signal.prekeys",
    props: {
      identityKey: { type: "string" },
      signedPrekey: { type: "unknown" },
      oneTimePrekeys: { type: "array", items: { type: "unknown" } },
    },
    required: ["identityKey", "signedPrekey", "oneTimePrekeys"],
  },
  {
    id: "ai.gftd.signal.otpks",
    props: {
      oneTimePrekeys: { type: "array", items: { type: "unknown" } },
    },
    required: ["oneTimePrekeys"],
  },
  {
    id: "ai.gftd.signal.groupKeyRotation",
    props: {
      convoId: { type: "string" },
      rotatedAt: { type: "string" },
    },
    required: ["convoId", "rotatedAt"],
  },
  {
    id: "ai.gftd.wproto.did",
    props: {
      did: { type: "string" },
      document: { type: "unknown" },
    },
    required: ["did", "document"],
  },
  {
    id: "ai.gftd.wproto.label",
    props: {
      label: { type: "string" },
      val: { type: "string" },
    },
    required: ["label", "val"],
  },
  {
    id: "ai.gftd.pds.profileIncomplete",
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
  { alias: "ai.gftd.convo.archiveConvo", source: "ai.gftd.convo.convo.archiveConvo" },
  { alias: "ai.gftd.convo.createConvo", source: "ai.gftd.convo.convo.createConvo" },
  { alias: "ai.gftd.convo.joinConvo", source: "ai.gftd.convo.convo.joinConvo" },
  { alias: "ai.gftd.convo.sendTyping", source: "ai.gftd.convo.convo.sendTyping" },
  { alias: "ai.gftd.convo.setProfile", source: "ai.gftd.convo.convo.setProfile" },
  { alias: "ai.gftd.convo.updateConvo", source: "ai.gftd.convo.convo.updateConvo" },
  { alias: "ai.gftd.convo.updatePresence", source: "ai.gftd.convo.convo.updatePresence" },
  { alias: "ai.gftd.convo.setEncryption", source: "ai.gftd.convo.convo.setConvoEncryption" },
  { alias: "ai.gftd.governance.checkAccess", source: "ai.gftd.governance.governance.checkAccess" },
  { alias: "ai.gftd.governance.getPolicy", source: "ai.gftd.governance.governance.getPolicy" },
  { alias: "ai.gftd.governance.registerMethodPolicy", source: "ai.gftd.governance.governance.registerMethodPolicy" },
  { alias: "ai.gftd.governance.registerPolicy", source: "ai.gftd.governance.governance.registerPolicy" },
  { alias: "ai.gftd.governance.resolveActorVisibility", source: "ai.gftd.governance.governance.resolveActorVisibility" },
  { alias: "ai.gftd.governance.setActorSensitivity", source: "ai.gftd.governance.governance.setActorSensitivity" },
  { alias: "ai.gftd.projector.addConvoMember", source: "ai.gftd.projector.projector.addConvoMember" },
  { alias: "ai.gftd.projector.addConvoTask", source: "ai.gftd.projector.projector.addConvoTask" },
  { alias: "ai.gftd.projector.archiveProjectConvo", source: "ai.gftd.projector.projector.archiveProjectConvo" },
  { alias: "ai.gftd.projector.completeConvoTask", source: "ai.gftd.projector.projector.completeConvoTask" },
  { alias: "ai.gftd.projector.getConvoProjectStatus", source: "ai.gftd.projector.projector.getConvoProjectStatus" },
  { alias: "ai.gftd.projector.getProjectConvo", source: "ai.gftd.projector.projector.getProjectConvo" },
  { alias: "ai.gftd.projector.listConvoTasks", source: "ai.gftd.projector.projector.listConvoTasks" },
  { alias: "ai.gftd.projector.listProjectConvos", source: "ai.gftd.projector.projector.listProjectConvos" },
  { alias: "ai.gftd.projector.newProjectConvo", source: "ai.gftd.projector.projector.newProjectConvo" },
  { alias: "ai.gftd.projector.sendProjectMessage", source: "ai.gftd.projector.projector.sendProjectMessage" },
  { alias: "ai.gftd.projector.updateProjectConvo", source: "ai.gftd.projector.projector.updateProjectConvo" },
  { alias: "ai.gftd.rtc.getVAPIDPublicKey", source: "ai.gftd.rtc.rtc.getVapidPublicKey" },
  { alias: "ai.gftd.rtc.hangupCall", source: "ai.gftd.rtc.rtc.hangupCall" },
  { alias: "ai.gftd.rtc.sendCallAnswer", source: "ai.gftd.rtc.rtc.sendCallAnswer" },
  { alias: "ai.gftd.rtc.sendCallICE", source: "ai.gftd.rtc.rtc.sendCallIce" },
  { alias: "ai.gftd.rtc.sendCallOffer", source: "ai.gftd.rtc.rtc.sendCallOffer" },
  { alias: "ai.gftd.rtc.subscribePush", source: "ai.gftd.rtc.rtc.subscribePush" },
  { alias: "ai.gftd.rtc.unsubscribePush", source: "ai.gftd.rtc.rtc.unsubscribePush" },
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
