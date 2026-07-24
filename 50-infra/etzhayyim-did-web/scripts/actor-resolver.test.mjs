// Node test for public/kotoba/actor-resolver.js — drives the browser resolver
// against the on-disk actors-v1 root + blocks via a file-backed fetch shim and a
// pre-initialised kotoba-wasm module. Verifies hydrate, record resolution, and
// per-actor DID self-verification (CID(didDocJson) === didDocCid) for all 28.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, resolve } from 'node:path';
import { ActorResolver } from '../public/kotoba/actor-resolver.js';

const here = dirname(fileURLToPath(import.meta.url));
const KOTOBA = resolve(here, '../public/kotoba');

// File-backed fetch shim: `${base}/<suffix>` → read KOTOBA/<suffix> from disk.
const fetchImpl = async (url) => {
  const path = resolve(KOTOBA, String(url).replace(/^kotoba\//, ''));
  const buf = readFileSync(path);
  return {
    ok: true,
    json: async () => JSON.parse(buf.toString('utf8')),
    arrayBuffer: async () => buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength),
  };
};

// Pre-initialise the wasm module once (browser path does this internally).
const wasm = await import(`${KOTOBA}/kotoba_wasm.js`);
await wasm.default(readFileSync(`${KOTOBA}/kotoba_wasm_bg.wasm`));

function makeResolver() {
  return new ActorResolver({ base: 'kotoba', fetchImpl, wasmModule: wasm });
}

test('init + listHandles returns all registered actors', async () => {
  const r = await makeResolver().init();
  const handles = r.listHandles();
  assert.ok(handles.length >= 28, `expected >=28 handles, got ${handles.length}`);
  assert.ok(handles.includes('yadori'));
  assert.ok(handles.includes('matsurigoto'));
});

test('resolveRecord reconstructs a full actor record', async () => {
  const r = await makeResolver().init();
  const rec = r.resolveRecord('yadori');
  assert.equal(rec.handle, 'yadori');
  assert.equal(rec.did, 'did:web:etzhayyim.com:actor:yadori');
  assert.ok(Array.isArray(rec.service)); // :actor/serviceJson parsed back to array
  assert.equal(rec.didDocCid?.startsWith('bafkrei'), true);
});

test('resolveDid self-verifies CID(didDocJson) === didDocCid for ALL actors', async () => {
  const r = await makeResolver().init();
  const handles = r.listHandles();
  let verified = 0;
  for (const h of handles) {
    const res = await r.resolveDid(h);
    assert.ok(res, `no DID for ${h}`);
    assert.equal(res.did, `did:web:etzhayyim.com:actor:${h}`);
    assert.equal(res.verified, true, `CID self-verify failed for ${h}`);
    verified++;
  }
  assert.ok(verified >= 28, `expected >=28 verified, got ${verified}`);
});

test('searchActors filters by handle / name / description', async () => {
  const r = await makeResolver().init();
  assert.equal(r.searchActors('yadori').length, 1);
  assert.ok(r.searchActors('did:web').length === 0); // not a substring of fields
  assert.ok(r.listActors().length >= 28);
});
