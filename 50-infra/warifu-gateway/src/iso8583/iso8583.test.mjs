// SPDX-License-Identifier: Apache-2.0
// Runnable: node src/iso8583/iso8583.test.mjs   (no deps)
// End-to-end Surface B flow (0100 -> authorize/settle -> 0110) over the in-memory substrate.
import assert from 'node:assert/strict';
import { handleIso8583Auth } from './handler.js';
import { DE39 } from '../common/iso8583-codec.js';
import { MemorySubstrate } from '../common/memory-substrate.js';
import { InMemoryIdempotencyStore } from '../common/idempotency.js';

let pass = 0;
const t = (name, fn) => Promise.resolve(fn()).then(() => { pass++; console.log(`  ok ${name}`); });

const lookup = () => 'did:m';
// DE4 '1000' cents @exp2 -> 10_000_000 USDC minor (10 USDC).
const msg = (over = {}) => ({
  mti: '0100',
  de2_pan: 'tok-A',
  de3_processingCode: '000000',
  de4_amount: '1000',
  de11_stan: 'stan-1',
  de42_merchantId: 'TERM01',
  de55_emv: '9F2701',
  ...over,
});
const deps = (phase2 = false) => ({
  substrate: new MemorySubstrate({ phase2 }).addCard('tok-A', 'acct-A', { balance: 100_000_000 }),
  idemStore: new InMemoryIdempotencyStore(),
});

await t('0100 internal-purchase approves -> DE39 00, merchant paid', async () => {
  const d = deps();
  const r = await handleIso8583Auth(msg(), d, lookup);
  assert.equal(r.de39_responseCode, DE39.APPROVE);
  assert.equal(d.substrate.bal['did:m'], 10_000_000);
});

await t('0100 external purchase (phase2 off) -> DE39 57 gated, substrate untouched', async () => {
  const d = deps();
  const r = await handleIso8583Auth(msg({ de11_stan: 's2' }), d, lookup, 'purchase');
  assert.equal(r.de39_responseCode, DE39.GATED);
  assert.equal(d.substrate.authorizeCalls, 0);
});

await t('0100 unknown purpose -> DE39 12 invalid', async () => {
  const d = deps();
  const r = await handleIso8583Auth(msg({ de11_stan: 's3' }), d, lookup, 'tip');
  assert.equal(r.de39_responseCode, DE39.INVALID);
});

await t('0100 insufficient funds -> DE39 05 decline', async () => {
  const d = deps();
  const r = await handleIso8583Auth(msg({ de11_stan: 's4', de4_amount: '999999999' }), d, lookup);
  assert.equal(r.de39_responseCode, DE39.DECLINE);
});

await t('0100 idempotent by DE11 STAN -> no double settle', async () => {
  const d = deps();
  const a = await handleIso8583Auth(msg({ de11_stan: 'dup' }), d, lookup);
  const b = await handleIso8583Auth(msg({ de11_stan: 'dup' }), d, lookup);
  assert.deepEqual(a, b);
  assert.equal(d.substrate.authorizeCalls, 1);
  assert.equal(d.substrate.bal['did:m'], 10_000_000);
});

console.log(`iso8583 e2e: ${pass} checks passed`);
