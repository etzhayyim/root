#!/usr/bin/env node
/**
 * gen-kotoba-actor-blocks.mjs — materialise the 28 actor-profile records into a
 * covering EAVT ProllyTree of content-addressed IPFS blocks, written as static
 * files under public/kotoba/blocks/<cid>, plus an `actors-v1.root.json` pointer.
 *
 * This is the "no node exposed" datomic path (ADR-2605312345 / 2606014600), the
 * exact sibling of gen-kotoba-blocks.mjs (yoro-social-v1): the browser kotoba-wasm
 * reads the root → fetches each /kotoba/blocks/<cid> from IPFS / the apex static
 * route → CID-verifies (ingestBlock) → hydrateFromProlly → datomicQ, entirely
 * client-side. NOTHING is read from a kotoba query node, the worker XRPC surface,
 * or CF KV — only self-verifying content + a root hash are published.
 *
 * SSoT = the same actor-profile seed the did:web Worker resolves from
 * (00-contracts/schemas/actor-profile-seed.kotoba.edn → materialised via
 * `npx nbb scripts/publish-actor-records.cljs` into ./out/actor-records/*.record.json).
 *
 * Run (after the wasm is built with exportBlocks — build-kotoba-wasm.sh):
 *   npx nbb scripts/publish-actor-records.cljs            # refresh out/actor-records
 *   node scripts/gen-kotoba-actor-blocks.mjs
 *
 * Datom schema (one entity per actor, e = "actor.<handle>"):
 *   :actor/handle :actor/did :actor/kind :actor/status :actor/glyph
 *   :actor/displayNameJa :actor/displayNameEn :actor/description :actor/tier
 *   :actor/performerType :actor/uiType :actor/primaryLexicon :actor/primarySchema
 *   :actor/createdAt :actor/source           — scalar string attributes
 *   :actor/serviceJson :actor/vmJson :actor/adrJson  — complex fields as JSON text
 */
import {
  readFileSync,
  writeFileSync,
  mkdirSync,
  existsSync,
  readdirSync,
} from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { createHash } from 'node:crypto';

// CIDv1 (raw, sha2-256) of bytes — identical to scripts/publish-actor-records.cljs
// + the worker's cid.ts, so a reader can recompute the DID-doc CID and verify the
// handle→didDoc binding with no server (ADR-2606015400 / 2606015600).
function _base32(bytes) {
  const A = 'abcdefghijklmnopqrstuvwxyz234567';
  let bits = 0,
    val = 0,
    out = '';
  for (const b of bytes) {
    val = (val << 8) | b;
    bits += 8;
    while (bits >= 5) {
      out += A[(val >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) out += A[(val << (5 - bits)) & 31];
  return out;
}
function cidV1Raw(buf) {
  const d = createHash('sha256').update(buf).digest();
  return 'b' + _base32(Buffer.concat([Buffer.from([0x01, 0x55, 0x12, 0x20]), d]));
}

const here = dirname(fileURLToPath(import.meta.url));
const apexPublic = resolve(here, '../public/kotoba');
const blocksDir = resolve(apexPublic, 'blocks');
const recordsDir = resolve(here, '../out/actor-records');
const GRAPH = 'actors-v1';

if (!existsSync(recordsDir)) {
  console.error(
    `✗ ${recordsDir} missing — run \`npx nbb scripts/publish-actor-records.cljs\` first.`,
  );
  process.exit(1);
}

const wasm = await import(`${apexPublic}/kotoba_wasm.js`);
await wasm.default(readFileSync(`${apexPublic}/kotoba_wasm_bg.wasm`));
const { KotobaNode } = wasm;

const hexToBytes = (h) => {
  const a = new Uint8Array(h.length / 2);
  for (let i = 0; i < a.length; i++) a[i] = parseInt(h.substr(i * 2, 2), 16);
  return a;
};

// ── record → datoms ─────────────────────────────────────────────────────────
// Scalar string fields become :actor/<field>; structured fields are stored as
// JSON text under an explicit *Json attribute so the browser can JSON.parse them.
const SCALAR = [
  'handle',
  'did',
  'kind',
  'status',
  'glyph',
  'displayNameJa',
  'displayNameEn',
  'description',
  'tier',
  'performerType',
  'uiType',
  'primaryLexicon',
  'primarySchema',
  'createdAt',
  'source',
];
const STRUCT = { service: 'serviceJson', vm: 'vmJson', adr: 'adrJson' };

function recordToDatoms(rec, didDocCanonical, didDocCid) {
  const e = `actor.${rec.handle}`;
  const out = [];
  for (const k of SCALAR) {
    const v = rec[k];
    if (v != null && v !== '') out.push([e, `:actor/${k}`, String(v)]);
  }
  for (const [k, attr] of Object.entries(STRUCT)) {
    const v = rec[k];
    if (v != null && (!Array.isArray(v) || v.length > 0)) {
      out.push([e, `:actor/${attr}`, JSON.stringify(v)]);
    }
  }
  // The DID document itself, defined IN the Datom log (worker-independent):
  //   :actor/didDocJson  — canonical DID-doc bytes (the CID preimage)
  //   :actor/didDocCid   — its content-addressed CIDv1 (self-verifying id)
  // A resolver (browser wasm) recomputes CID(didDocJson) and checks == didDocCid,
  // anchoring the handle→DID binding with no TLS / no server (ADR-2606015400/15600).
  out.push([e, ':actor/didDocJson', didDocCanonical]);
  out.push([e, ':actor/didDocCid', didDocCid]);
  return out;
}

const recordFiles = readdirSync(recordsDir)
  .filter((f) => f.endsWith('.record.json'))
  .sort();
const records = recordFiles.map((f) =>
  JSON.parse(readFileSync(resolve(recordsDir, f), 'utf8')),
);

// Load the materialised canonical DID doc + CID per actor and self-verify the
// content-addressed binding (CID(canonical) === published .diddoc.cid) BEFORE it
// goes into the log — this is exactly the check the wasm resolver re-runs.
const datoms = records.flatMap((rec) => {
  const h = rec.handle;
  const canonical = readFileSync(
    resolve(recordsDir, `${h}.did.canonical.json`),
    'utf8',
  ).trim();
  const cid = readFileSync(resolve(recordsDir, `${h}.diddoc.cid`), 'utf8').trim();
  const recomputed = cidV1Raw(Buffer.from(canonical, 'utf8'));
  if (recomputed !== cid) {
    console.error(
      `✗ ${h}: DID-doc CID mismatch (file ${cid} ≠ recomputed ${recomputed})`,
    );
    process.exit(1);
  }
  return recordToDatoms(rec, canonical, cid);
});
console.log(`actors: ${records.length} | datoms: ${datoms.length}`);

// WRITE path: assert every datom, then commit → ProllyTree root + blocks.
const w = new KotobaNode();
for (const [e, a, v] of datoms) w.assert(e, a, v);
const root = w.commit();
const blocks = JSON.parse(w.exportBlocks());
const bytes = blocks.reduce((s, b) => s + b.hex.length / 2, 0);
console.log(`committed root: ${root}`);
console.log(`blocks: ${blocks.length} | ${(bytes / 1024).toFixed(1)} KiB`);

// VERIFY round-trip BEFORE publishing: fresh node, ingest blocks from CID,
// hydrate by traversing the tree, query actors back out.
const r = new KotobaNode();
for (const b of blocks) r.ingestBlock(b.cid, hexToBytes(b.hex));
const applied = r.hydrateFromProlly(root);
const q = r.datomicQ('{:find [?h] :where [[?e :actor/handle ?h]]}', '[]');
let handles = 0;
try {
  const j = JSON.parse(q);
  handles = (j.rows_edn || j.rows || []).length;
} catch {}
console.log(`round-trip: hydrated ${applied} datoms | datomicQ handles=${handles}`);
if (applied !== datoms.length || handles !== records.length) {
  console.error(
    `✗ round-trip mismatch (datoms ${applied}/${datoms.length}, handles ${handles}/${records.length}) — NOT writing blocks`,
  );
  process.exit(1);
}

// Worker-independent DID RESOLUTION proof: from the hydrated blocks alone,
// pull a sample actor's :actor/didDocJson + :actor/didDocCid and re-verify the
// content-addressed binding — exactly what the browser wasm does at resolve time.
const sample = 'yadori';
const rq = JSON.parse(
  r.datomicQ(
    `{:find [?doc ?cid] :where [[?e :actor/handle "${sample}"] [?e :actor/didDocJson ?doc] [?e :actor/didDocCid ?cid]]}`,
    '[]',
  ),
);
const row = (rq.rows_edn || rq.rows || [])[0] || [];
const unedn = (s) => (typeof s === 'string' && s.startsWith('"') ? JSON.parse(s) : s);
const resolvedDoc = unedn(row[0]);
const resolvedCid = unedn(row[1]);
const didId = resolvedDoc ? JSON.parse(resolvedDoc).id : null;
const cidOk = resolvedDoc && cidV1Raw(Buffer.from(resolvedDoc, 'utf8')) === resolvedCid;
console.log(
  `did-resolve(${sample}): id=${didId} cid=${resolvedCid} self-verify=${cidOk ? 'OK' : 'FAIL'}`,
);
if (!didId || !cidOk) {
  console.error('✗ in-wasm DID resolution/self-verification failed — NOT writing blocks');
  process.exit(1);
}

// Publish: write each block as a content-addressed file. ADDITIVE — the blocks
// dir is shared across graphs (content-addressed; same CID ⇒ same bytes), so we
// must NOT wipe it (that would destroy the yoro-social-v1 blocks). Unlike
// gen-kotoba-blocks.mjs, this generator only adds its own CIDs.
mkdirSync(blocksDir, { recursive: true });
for (const b of blocks) writeFileSync(resolve(blocksDir, b.cid), hexToBytes(b.hex));
const manifest = {
  graph: GRAPH,
  root,
  blocks: blocks.map((b) => b.cid),
  datoms: datoms.length,
  actors: records.length,
  handles: records.map((x) => x.handle).sort(),
  source: '00-contracts/schemas/actor-profile-seed.kotoba.edn (snapshot)',
};
writeFileSync(resolve(apexPublic, `${GRAPH}.root.json`), JSON.stringify(manifest) + '\n');
console.log(`✓ wrote ${blocks.length} blocks → ${blocksDir}`);
console.log(`✓ wrote root pointer → ${apexPublic}/${GRAPH}.root.json  (root ${root})`);

// Emit STATIC, worker-independent did.json + profile.json per actor (step 3,
// content-addressed DID). Cloudflare serves files under ./public BEFORE the
// Worker runs, so GET /actor/<h>/did.json is answered straight from the edge
// with no Worker logic, no CF KV, and no bundled ACTORS_V1_RECORDS projection —
// the did:web document is just the content-addressed bytes (its CIDv1 is the
// :actor/didDocCid datom in the actors-v1 log; the browser ActorResolver
// re-verifies CID(didDocJson)===didDocCid). Entity-actors + human members keep
// the Worker's dynamic path (they have no static file). The byte content here is
// identical to the Worker's previous toDidDoc / toGetProfileView output, so
// existing did:web + REST profile consumers see no change.
let staticCount = 0;
for (const rec of records) {
  const dir = resolve(here, `../public/actor/${rec.handle}`);
  mkdirSync(dir, { recursive: true });
  const didJson = readFileSync(resolve(recordsDir, `${rec.handle}.did.json`), 'utf8');
  const profileJson = readFileSync(
    resolve(recordsDir, `${rec.handle}.profile.json`),
    'utf8',
  );
  writeFileSync(resolve(dir, 'did.json'), didJson.endsWith('\n') ? didJson : didJson + '\n');
  writeFileSync(
    resolve(dir, 'profile.json'),
    profileJson.endsWith('\n') ? profileJson : profileJson + '\n',
  );
  staticCount++;
}
console.log(
  `✓ wrote ${staticCount}×2 static files → public/actor/<h>/{did.json,profile.json} (CF-served, worker-independent)`,
);
