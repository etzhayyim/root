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
 * `node scripts/publish-actor-records.mjs` into ./out/actor-records/*.record.json).
 *
 * Run (after the wasm is built with exportBlocks — build-kotoba-wasm.sh):
 *   node scripts/publish-actor-records.mjs            # refresh out/actor-records
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

const here = dirname(fileURLToPath(import.meta.url));
const apexPublic = resolve(here, '../public/kotoba');
const blocksDir = resolve(apexPublic, 'blocks');
const recordsDir = resolve(here, '../out/actor-records');
const GRAPH = 'actors-v1';

if (!existsSync(recordsDir)) {
  console.error(
    `✗ ${recordsDir} missing — run \`node scripts/publish-actor-records.mjs\` first.`,
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

function recordToDatoms(rec) {
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
  return out;
}

const recordFiles = readdirSync(recordsDir)
  .filter((f) => f.endsWith('.record.json'))
  .sort();
const records = recordFiles.map((f) =>
  JSON.parse(readFileSync(resolve(recordsDir, f), 'utf8')),
);
const datoms = records.flatMap(recordToDatoms);
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
