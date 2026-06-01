// SPDX-License-Identifier: Apache-2.0
// Runnable with: node src/common/gateway.test.mjs   (no test framework / no deps)
import assert from 'node:assert/strict';
import { InMemoryIdempotencyStore, withIdempotency } from './idempotency.js';
import { DE39, toUsdcMinor, decisionToDe39, fundingFromProcessingCode } from './iso8583-codec.js';

let pass = 0;
const t = (name, fn) => { return Promise.resolve(fn()).then(() => { pass++; console.log(`  ok ${name}`); }); };

await t('idempotency: fn runs once, replay returns cached result', async () => {
  const store = new InMemoryIdempotencyStore();
  let calls = 0;
  const run = () => withIdempotency(store, 'k1', async () => { calls++; return { authId: 'auth-X' }; });
  const a = await run();
  const b = await run();
  assert.deepEqual(a, b);
  assert.equal(calls, 1, 'fn must execute exactly once per key');
});

await t('idempotency: distinct keys execute independently', async () => {
  const store = new InMemoryIdempotencyStore();
  let calls = 0;
  await withIdempotency(store, 'k1', async () => { calls++; return 1; });
  await withIdempotency(store, 'k2', async () => { calls++; return 2; });
  assert.equal(calls, 2);
});

await t('idempotency: missing key is refused', async () => {
  const store = new InMemoryIdempotencyStore();
  await assert.rejects(() => withIdempotency(store, '', async () => 1), /key required/);
});

await t('idempotency: in-flight key is refused', async () => {
  const store = new InMemoryIdempotencyStore();
  store.begin('k1'); // simulate a concurrent request mid-flight
  await assert.rejects(() => withIdempotency(store, 'k1', async () => 1), /in flight/);
});

await t('idempotency: failed attempt clears key so retry is allowed (money never moved)', async () => {
  const store = new InMemoryIdempotencyStore();
  let calls = 0;
  await assert.rejects(() =>
    withIdempotency(store, 'k1', async () => { calls++; throw new Error('substrate down'); }));
  const ok = await withIdempotency(store, 'k1', async () => { calls++; return 'ok'; });
  assert.equal(ok, 'ok');
  assert.equal(calls, 2, 'retry after failure must re-run');
});

await t('iso8583: amount scales terminal cents -> USDC 6dp minor', () => {
  assert.equal(toUsdcMinor('1200', 2), 12_000_000); // $12.00 -> 12.000000 USDC
  assert.equal(toUsdcMinor('1', 2), 10_000);
  assert.ok(Number.isNaN(toUsdcMinor('abc', 2)));
});

await t('iso8583: decision -> DE39 response codes', () => {
  assert.equal(decisionToDe39('approve'), DE39.APPROVE);   // 00
  assert.equal(decisionToDe39('gated'), DE39.GATED);       // 57
  assert.equal(decisionToDe39('decline', true), DE39.INVALID); // 12 (unknown purpose)
  assert.equal(decisionToDe39('decline', false), DE39.DECLINE); // 05
});

await t('iso8583: processing code -> funding (R0 conservative)', () => {
  assert.equal(fundingFromProcessingCode('000000'), 'debit');
});

console.log(`gateway (idempotency + iso8583): ${pass} checks passed`);
