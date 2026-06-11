#!/usr/bin/env node
/**
 * update-lexicon-schemas.mjs
 * Overwrites AT Protocol Lexicon JSON files in 00-contracts/lexicons/
 * with properly typed schemas derived from PDS handler analysis.
 */
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';

const ROOT = join(import.meta.dirname, '..', '..', '..');
const LEXICONS_DIR = join(ROOT, '00-contracts', 'lexicons');

// --- Schema definitions ---

const rkeyUriCid = {
  rkey: { type: 'string' },
  uri: { type: 'string' },
  cid: { type: 'string' },
};
const rkeyUriCidRequired = ['rkey', 'uri', 'cid'];

function nsidToPath(nsid) {
  const parts = nsid.split('.');
  const methodName = parts.pop();
  return join(LEXICONS_DIR, ...parts, `${methodName}.json`);
}

function buildQuery(nsid, params, response) {
  const doc = {
    lexicon: 1,
    id: nsid,
    defs: {
      main: {
        type: 'query',
      },
    },
  };
  const main = doc.defs.main;

  // parameters
  const paramProps = {};
  const paramRequired = [];
  for (const [k, v] of Object.entries(params)) {
    const optional = k.endsWith('?');
    const name = optional ? k.slice(0, -1) : k;
    paramProps[name] = typeDef(v);
    if (!optional) paramRequired.push(name);
  }
  main.parameters = { type: 'params', properties: paramProps };
  if (paramRequired.length > 0) main.parameters.required = paramRequired;

  // output
  const { props: outProps, required: outReq } = buildObjSchema(response);
  const outSchema = { type: 'object', properties: outProps };
  if (outReq.length > 0) outSchema.required = outReq;
  main.output = { encoding: 'application/json', schema: outSchema };

  return doc;
}

function buildProcedure(nsid, params, response) {
  const doc = {
    lexicon: 1,
    id: nsid,
    defs: {
      main: {
        type: 'procedure',
      },
    },
  };
  const main = doc.defs.main;

  // input
  const { props: inProps, required: inReq } = buildObjSchema(params);
  if (Object.keys(inProps).length > 0) {
    const inSchema = { type: 'object', properties: inProps };
    if (inReq.length > 0) inSchema.required = inReq;
    main.input = { encoding: 'application/json', schema: inSchema };
  }

  // output
  const { props: outProps, required: outReq } = buildObjSchema(response);
  const outSchema = { type: 'object', properties: outProps };
  if (outReq.length > 0) outSchema.required = outReq;
  main.output = { encoding: 'application/json', schema: outSchema };

  return doc;
}

function buildEmpty(nsid, type) {
  const doc = {
    lexicon: 1,
    id: nsid,
    defs: {
      main: {
        type,
        ...(type === 'query'
          ? { parameters: { type: 'params', properties: {} } }
          : {}),
        output: {
          encoding: 'application/json',
          schema: { type: 'object', properties: {} },
        },
      },
    },
  };
  return doc;
}

function typeDef(t) {
  if (t === 'string') return { type: 'string' };
  if (t === 'number') return { type: 'number' };
  if (t === 'integer') return { type: 'integer' };
  if (t === 'boolean') return { type: 'boolean' };
  if (t === 'object') return { type: 'object' };
  if (t === 'array') return { type: 'array', items: { type: 'object' } };
  if (t === 'string[]') return { type: 'array', items: { type: 'string' } };
  return { type: 'string' };
}

function buildObjSchema(obj) {
  const props = {};
  const required = [];
  for (const [k, v] of Object.entries(obj)) {
    const optional = k.endsWith('?');
    const name = optional ? k.slice(0, -1) : k;
    props[name] = typeDef(v);
    if (!optional) required.push(name);
  }
  return { props, required };
}

function writeLexicon(doc) {
  const filePath = nsidToPath(doc.id);
  mkdirSync(dirname(filePath), { recursive: true });
  writeFileSync(filePath, JSON.stringify(doc, null, 2) + '\n');
  return filePath;
}

// ========================
// All NSID definitions
// ========================

const definitions = [];

// --- com.etzhayyim.consent.consent ---
const consentNs = 'com.etzhayyim.consent.consent';
for (const m of ['listConsentGrants', 'resolveConsent']) {
  definitions.push(buildEmpty(`${consentNs}.${m}`, 'query'));
}
for (const m of ['requestConsent', 'revokeConsent']) {
  definitions.push(buildEmpty(`${consentNs}.${m}`, 'procedure'));
}

// --- com.etzhayyim.convo.convo ---
const convoNs = 'com.etzhayyim.convo.convo';

// Empty handlers
for (const m of ['createSession', 'diff', 'fetchBlocks', 'sendSessionMessage']) {
  definitions.push(buildEmpty(`${convoNs}.${m}`, 'procedure'));
}
for (const m of ['getProfile', 'getSession', 'getSyncState', 'listSessions']) {
  definitions.push(buildEmpty(`${convoNs}.${m}`, 'query'));
}

// Procedures with schemas
definitions.push(buildProcedure(`${convoNs}.archiveConvo`, { convoId: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.createChannel`, { name: 'string', 'kind?': 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.createConvo`, { name: 'string', 'kind?': 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.createDm`, { peerDid: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.editMessage`, { convoId: 'string', messageId: 'string', text: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.inviteConvoMember`, { convoId: 'string', memberDid: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.joinConvo`, { convoId: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.leaveConvo`, { convoId: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.markRead`, { convoId: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.react`, { convoId: 'string', messageId: 'string', emoji: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.redactMessage`, { convoId: 'string', messageId: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.search`, { q: 'string', 'convoId?': 'string', 'limit?': 'number' }, { results: 'array' }));
definitions.push(buildProcedure(`${convoNs}.send`, { convoId: 'string', text: 'string', 'kind?': 'string', 'contentType?': 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.sendMessage`, { convoId: 'string', 'text?': 'string', 'payload?': 'string', 'kind?': 'string', 'contentType?': 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.sendTyping`, { convoId: 'string' }, { ok: 'boolean' }));
definitions.push(buildProcedure(`${convoNs}.setConvoEncryption`, { convoId: 'string', 'mode?': 'string' }, { convoId: 'string', encryption: 'string' }));
definitions.push(buildProcedure(`${convoNs}.setProfile`, {}, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.unreact`, { convoId: 'string', messageId: 'string', emoji: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.updateConvo`, { convoId: 'string', 'name?': 'string', 'description?': 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.updateConvoMemberRole`, { convoId: 'string', memberDid: 'string', role: 'string' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${convoNs}.updatePresence`, { convoId: 'string', 'status?': 'string' }, { ...rkeyUriCid }));

// Queries with schemas
definitions.push(buildQuery(`${convoNs}.getConvo`, { convoId: 'string' }, { convo: 'object' }));
definitions.push(buildQuery(`${convoNs}.getHistory`, { convoId: 'string', 'limit?': 'number', 'cursor?': 'string' }, { messages: 'array', cursor: 'string' }));
definitions.push(buildQuery(`${convoNs}.getReactions`, { convoId: 'string', messageId: 'string' }, { reactions: 'array' }));
definitions.push(buildQuery(`${convoNs}.getThread`, { convoId: 'string', messageId: 'string' }, { thread: 'array' }));
definitions.push(buildQuery(`${convoNs}.getUnread`, {}, { count: 'number' }));
definitions.push(buildQuery(`${convoNs}.listConvoMembers`, { convoId: 'string' }, { members: 'array' }));
definitions.push(buildQuery(`${convoNs}.listConvos`, { 'limit?': 'number', 'cursor?': 'string' }, { convos: 'array', cursor: 'string' }));
definitions.push(buildQuery(`${convoNs}.listEnvelopes`, { convoId: 'string', 'limit?': 'number', 'cursor?': 'string' }, { envelopes: 'array', cursor: 'string' }));
definitions.push(buildQuery(`${convoNs}.listPresence`, { convoId: 'string' }, { presence: 'array' }));
definitions.push(buildQuery(`${convoNs}.listPublicConvos`, { 'limit?': 'number', 'cursor?': 'string' }, { convos: 'array', cursor: 'string' }));

// --- com.etzhayyim.projector.projector ---
const projNs = 'com.etzhayyim.projector.projector';

definitions.push(buildProcedure(`${projNs}.newProjectConvo`, {
  name: 'string', 'description?': 'string', 'kind?': 'string', 'members?': 'string[]', 'parentProjectUri?': 'string',
}, {
  convoId: 'string', projectId: 'string', did: 'string', name: 'string', email: 'string', kind: 'string', depth: 'number',
}));
definitions.push(buildQuery(`${projNs}.getProjectConvo`, { convoId: 'string' }, {
  convo: 'object', project: 'object', taskSummary: 'object', totalTasks: 'number', members: 'array', children: 'array', depth: 'number',
}));
definitions.push(buildQuery(`${projNs}.listProjectConvos`, { 'offset?': 'number', 'limit?': 'number', 'parentUri?': 'string' }, {
  convos: 'array', total: 'number', offset: 'number', limit: 'number',
}));
definitions.push(buildProcedure(`${projNs}.updateProjectConvo`, { convoId: 'string', 'name?': 'string', 'description?': 'string', 'status?': 'string' }, {
  status: 'string', convoId: 'string',
}));
definitions.push(buildProcedure(`${projNs}.archiveProjectConvo`, { convoId: 'string' }, {
  status: 'string', convoId: 'string', projectId: 'string', archivedChildren: 'number',
}));
definitions.push(buildProcedure(`${projNs}.sendProjectMessage`, { convoId: 'string', text: 'string' }, {
  reply: 'string', messages: 'array',
}));
definitions.push(buildQuery(`${projNs}.listConvoTasks`, { convoId: 'string', 'status?': 'string', 'offset?': 'number', 'limit?': 'number' }, {
  tasks: 'array', total: 'number', offset: 'number', limit: 'number',
}));
definitions.push(buildProcedure(`${projNs}.addConvoTask`, { convoId: 'string', title: 'string', 'priority?': 'string', 'assigneeDid?': 'string', 'dueDate?': 'string' }, {
  taskId: 'string', title: 'string', status: 'string',
}));
definitions.push(buildProcedure(`${projNs}.completeConvoTask`, { convoId: 'string', taskId: 'string' }, {
  taskId: 'string', status: 'string',
}));
definitions.push(buildProcedure(`${projNs}.addConvoMember`, { convoId: 'string', memberDid: 'string', 'role?': 'string' }, {
  memberId: 'string', status: 'string',
}));
definitions.push(buildQuery(`${projNs}.getConvoProjectStatus`, { convoId: 'string' }, {
  project: 'object', taskSummary: 'object', totalTasks: 'number', childCount: 'number',
}));

// --- com.etzhayyim.governance.governance ---
const govNs = 'com.etzhayyim.governance.governance';

definitions.push(buildQuery(`${govNs}.checkAccess`, { targetDid: 'string', 'method?': 'string' }, { allowed: 'boolean', 'reason?': 'string' }));
definitions.push(buildQuery(`${govNs}.getActorSensitivity`, {}, { sensitivity: 'string' }));
definitions.push(buildQuery(`${govNs}.getPolicy`, { name: 'string', 'ownerDid?': 'string' }, { name: 'string', rules: 'object', updatedAt: 'string' }));
definitions.push(buildQuery(`${govNs}.listPolicies`, { 'limit?': 'number' }, { policies: 'array' }));
definitions.push(buildProcedure(`${govNs}.registerMethodPolicy`, { method: 'string', 'requiredRoles?': 'array', 'trustLevel?': 'string' }, { method: 'string', registered: 'boolean' }));
definitions.push(buildProcedure(`${govNs}.registerPolicy`, { name: 'string', rules: 'object' }, { name: 'string', registered: 'boolean' }));
definitions.push(buildQuery(`${govNs}.resolveActorVisibility`, { actor: 'string' }, { sensitivity: 'string', tier: 'number', visible: 'boolean' }));
definitions.push(buildProcedure(`${govNs}.setActorSensitivity`, { sensitivity: 'string' }, { did: 'string', sensitivity: 'string' }));

// --- com.etzhayyim.rtc.rtc ---
const rtcNs = 'com.etzhayyim.rtc.rtc';

definitions.push(buildQuery(`${rtcNs}.getVapidPublicKey`, {}, { publicKey: 'string' }));
definitions.push(buildProcedure(`${rtcNs}.hangupCall`, { convoId: 'string', 'callId?': 'string', 'reason?': 'string' }, { ok: 'boolean', signalType: 'string', convoId: 'string' }));
definitions.push(buildProcedure(`${rtcNs}.sendCallAnswer`, { convoId: 'string', 'callId?': 'string', sdp: 'string' }, { ok: 'boolean', signalType: 'string', convoId: 'string' }));
definitions.push(buildProcedure(`${rtcNs}.sendCallIce`, { convoId: 'string', 'callId?': 'string', 'candidate?': 'string', 'sdpMid?': 'string', 'sdpMLineIndex?': 'number' }, { ok: 'boolean', signalType: 'string', convoId: 'string' }));
definitions.push(buildProcedure(`${rtcNs}.sendCallOffer`, { convoId: 'string', targetDid: 'string', sdp: 'string', 'callId?': 'string', 'mediaType?': 'string' }, { ok: 'boolean', signalType: 'string', convoId: 'string' }));
definitions.push(buildProcedure(`${rtcNs}.subscribePush`, { subscription: 'object' }, { ...rkeyUriCid }));
definitions.push(buildProcedure(`${rtcNs}.unsubscribePush`, { 'endpoint?': 'string' }, { unsubscribed: 'boolean' }));

// --- com.etzhayyim.signal.signal ---
const sigNs = 'com.etzhayyim.signal.signal';

definitions.push(buildProcedure(`${sigNs}.buildPreKeyBundle`, { did: 'string' }, { bundle: 'object' }));
definitions.push(buildProcedure(`${sigNs}.generateIdentity`, {}, { identityKey: 'string' }));
definitions.push(buildProcedure(`${sigNs}.generateOneTimePrekey`, {}, { prekey: 'object' }));
definitions.push(buildProcedure(`${sigNs}.generateSignedPrekey`, {}, { signedPrekey: 'object' }));
definitions.push(buildProcedure(`${sigNs}.groupDecrypt`, { convoId: 'string', ciphertext: 'string', senderDid: 'string' }, { plaintext: 'string' }));
definitions.push(buildProcedure(`${sigNs}.groupEncrypt`, { convoId: 'string', plaintext: 'string' }, { ciphertext: 'string' }));
definitions.push(buildProcedure(`${sigNs}.groupInitSender`, { convoId: 'string' }, { distributionMessage: 'string' }));
definitions.push(buildProcedure(`${sigNs}.groupProcessDistribution`, { convoId: 'string', senderDid: 'string', distributionMessage: 'string' }, { processed: 'boolean' }));
definitions.push(buildProcedure(`${sigNs}.ratchetDecrypt`, { senderDid: 'string', ciphertext: 'string' }, { plaintext: 'string' }));
definitions.push(buildProcedure(`${sigNs}.ratchetEncrypt`, { recipientDid: 'string', plaintext: 'string' }, { ciphertext: 'string' }));
definitions.push(buildProcedure(`${sigNs}.ratchetInitReceiver`, { senderDid: 'string', preKeyMessage: 'string' }, { initialized: 'boolean' }));
definitions.push(buildProcedure(`${sigNs}.ratchetInitSender`, { recipientDid: 'string', bundle: 'object' }, { preKeyMessage: 'string' }));
definitions.push(buildProcedure(`${sigNs}.x3dhInitiate`, { recipientDid: 'string' }, { ephemeralKey: 'string', preKeyMessage: 'string' }));
definitions.push(buildProcedure(`${sigNs}.x3dhRespond`, { senderDid: 'string', ephemeralKey: 'string', preKeyMessage: 'string' }, { sessionEstablished: 'boolean' }));

// ========================
// Write all files
// ========================

let count = 0;
for (const doc of definitions) {
  const p = writeLexicon(doc);
  count++;
  console.log(`  wrote ${doc.id}`);
}

console.log(`\nTotal: ${count} lexicon files written.`);
