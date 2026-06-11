// SPDX-License-Identifier: Apache-2.0
// Runnable: node src/nfc/nfc.test.mjs   (no deps)
// End-to-end Surface C flow (HCE tap -> authorize/settle) over the in-memory substrate.
import assert from 'node:assert/strict';
import { handleNfcTap } from './handler.js';
import { MemorySubstrate } from '../common/memory-substrate.js';
import { InMemoryIdempotencyStore } from '../common/idempotency.js';

let pass = 0;
const t = (name, fn) => Promise.resolve(fn()).then(() => { pass++; console.log(`  ok ${name}`); });

const tap = (over = {}) => ({
  cardToken: 'tok-A',
  amountUsdc: 250_000,
  merchantDid: 'did:m',
  emvCryptogram: '9F2601AABB',
  passkeyAssertion: 'webauthn-assertion',
  stan: 'tap-1',
  ...over,
});
const deps = (phase2 = false) => ({
  substrate: new MemorySubstrate({ phase2 }).addCard('tok-A', 'acct-A', { balance: 1_000_000 }),
  idemStore: new InMemoryIdempotencyStore(),
});

await t('tap internal-purchase approved, merchant paid (fee 0)', async () => {
  const d = deps();
  const r = await handleNfcTap(tap(), d);
  assert.equal(r.approved, true);
  assert.ok(r.tx);
  assert.equal(d.substrate.bal['did:m'], 250_000);
});

await t('tap external purchase (phase2 off) -> not approved, gated, substrate untouched', async () => {
  const d = deps();
  const r = await handleNfcTap(tap({ stan: 't2' }), d, 'purchase');
  assert.equal(r.approved, false);
  assert.equal(r.gate, 'gated');
  assert.equal(d.substrate.authorizeCalls, 0);
});

await t('tap insufficient funds -> not approved', async () => {
  const d = deps();
  const r = await handleNfcTap(tap({ stan: 't3', amountUsdc: 9_000_000 }), d);
  assert.equal(r.approved, false);
});

await t('tap idempotent by STAN -> no double charge', async () => {
  const d = deps();
  const a = await handleNfcTap(tap({ stan: 'dup' }), d);
  const b = await handleNfcTap(tap({ stan: 'dup' }), d);
  assert.deepEqual(a, b);
  assert.equal(d.substrate.authorizeCalls, 1);
  assert.equal(d.substrate.bal['did:m'], 250_000);
});

console.log(`nfc e2e: ${pass} checks passed`);
