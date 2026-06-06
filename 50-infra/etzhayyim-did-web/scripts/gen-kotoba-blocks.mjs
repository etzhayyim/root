#!/usr/bin/env node
/**
 * gen-kotoba-blocks.mjs — materialise the yoro-social-v1 post Datoms into a
 * covering EAVT ProllyTree of content-addressed IPFS blocks, written as static
 * files under public/kotoba/blocks/<cid>, plus a published root pointer.
 *
 * This is the "no node exposed" path (ADR-2605312345 / 2606014600): the browser
 * kotoba-wasm reads root → missingBlockCids → fetches each /kotoba/blocks/<cid>
 * → CID-verifies (ingestBlock) → hydrateFromProlly → datomicQ. The only thing
 * published is self-verifying content + a root hash; no kotoba query node.
 *
 * Source datoms = the same seed the JSON path used (svelte/public/kotoba/
 * seed-datoms.json); blocks + root are written into THIS Worker's public/kotoba
 * so the apex serves them directly (static-asset route).
 *
 * Run after the wasm is (re)built with exportBlocks (build-kotoba-wasm.sh):
 *   node scripts/gen-kotoba-blocks.mjs
 */
import { readFileSync, writeFileSync, mkdirSync, rmSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';

const here = dirname(fileURLToPath(import.meta.url));
const apexPublic = resolve(here, '../public/kotoba');
const blocksDir = resolve(apexPublic, 'blocks');
const seedPath = resolve(
  here,
  '../../../60-apps/etzhayyim-project-yoro/appview/yoro-ui-g00h5zto/svelte/public/kotoba/seed-datoms.json',
);
const GRAPH = 'yoro-social-v1';

const wasm = await import(`${apexPublic}/kotoba_wasm.js`);
await wasm.default(readFileSync(`${apexPublic}/kotoba_wasm_bg.wasm`));
const { KotobaNode } = wasm;

const hexToBytes = (h) => {
  const a = new Uint8Array(h.length / 2);
  for (let i = 0; i < a.length; i++) a[i] = parseInt(h.substr(i * 2, 2), 16);
  return a;
};

const seed = JSON.parse(readFileSync(seedPath, 'utf8'));
console.log(`seed datoms: ${seed.length}`);

// WRITE path: assert every datom into the write-set, then commit → ProllyTree.
const w = new KotobaNode();
for (const d of seed) {
  const val = JSON.parse(d.v_edn); // decoded value (string)
  w.assert(d.e, d.a, typeof val === 'string' ? val : JSON.stringify(val));
}
const root = w.commit();
const blocks = JSON.parse(w.exportBlocks());
const bytes = blocks.reduce((s, b) => s + b.hex.length / 2, 0);
console.log(`committed root: ${root}`);
console.log(`blocks: ${blocks.length} | ${(bytes / 1024).toFixed(1)} KiB`);

// VERIFY round-trip BEFORE publishing: fresh node, ingest blocks from CID,
// hydrate by traversing the tree, query posts.
const r = new KotobaNode();
for (const b of blocks) r.ingestBlock(b.cid, hexToBytes(b.hex));
const applied = r.hydrateFromProlly(root);
const q = r.datomicQ('{:find [?e] :where [[?e :yoro.post/uri ?u]]}', '[]');
let posts = 0;
try {
  const j = JSON.parse(q);
  posts = (j.rows_edn || j.rows || []).length;
} catch {}
console.log(`round-trip: hydrated ${applied} datoms | datomicQ posts=${posts}`);
if (applied !== seed.length || posts === 0) {
  console.error('✗ round-trip mismatch — NOT writing blocks');
  process.exit(1);
}

// Publish: clean blocks dir, write each block as a content-addressed file.
if (existsSync(blocksDir)) rmSync(blocksDir, { recursive: true });
mkdirSync(blocksDir, { recursive: true });
for (const b of blocks) writeFileSync(resolve(blocksDir, b.cid), hexToBytes(b.hex));
const manifest = {
  graph: GRAPH,
  root,
  blocks: blocks.map((b) => b.cid),
  datoms: seed.length,
  posts,
  source: 'app.bsky.feed.getFeed (snapshot)',
};
writeFileSync(resolve(apexPublic, `${GRAPH}.root.json`), JSON.stringify(manifest) + '\n');
console.log(`✓ wrote ${blocks.length} blocks → ${blocksDir}`);
console.log(`✓ wrote root pointer → ${apexPublic}/${GRAPH}.root.json  (root ${root})`);
