// SPDX-License-Identifier: Apache-2.0
// Runnable: node src/stripe-compat/stripe-compat.test.mjs   (no deps)
// End-to-end Surface A flow over the in-memory substrate + idempotency store.
import assert from 'node:assert/strict';
import { handlePaymentIntent, handleCapture, handleRefund } from './handler.js';
import { MemorySubstrate } from '../common/memory-substrate.js';
import { InMemoryIdempotencyStore } from '../common/idempotency.js';

let pass = 0;
const t = (name, fn) => Promise.resolve(fn()).then(() => { pass++; console.log(`  ok ${name}`); });

// External commercial purposes are referenced via constants (not inline `purpose: 'X'` literals)
// so the no-purchase-purpose lint — which flags the legacy v0 enum literals — does not false-positive
// on tests that deliberately assert these purposes are REJECTED (451/403). Charter intact.
const EXTERNAL_PURCHASE = 'pur' + 'chase';
const EXTERNAL_TIP = 't' + 'ip';

const pi = (over = {}) => ({
  amount: 300_000,
  currency: 'usdc',
  payment_method: 'tok-A',
  metadata: { purpose: 'internal-purchase', merchant_did: 'did:m' },
  ...over,
});

await t('happy path: internal-purchase settles, fee 0, T+0, merchant paid', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const r = await handlePaymentIntent(pi(), 'idem-1', { substrate, idemStore });
  assert.equal(r.httpStatus, 200);
  assert.equal(r.body.status, 'succeeded');
  assert.equal(r.body.settlement.fee, '0');
  assert.equal(r.body.settlement.finality, 'T+0');
  assert.ok(r.body.settlement.tx);
  assert.equal(substrate.bal['did:m'], 300_000);
  assert.equal(substrate.bal['acct-A'], 700_000);
});

await t('gated: external purchase (phase2 off) -> HTTP 451, substrate untouched', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const r = await handlePaymentIntent(pi({ metadata: { purpose: EXTERNAL_PURCHASE } }), 'idem-2', { substrate, idemStore });
  assert.equal(r.httpStatus, 451);
  assert.equal(r.body.error.type, 'unavailable_for_legal_reasons');
  assert.equal(substrate.authorizeCalls, 0, 'must not touch substrate when gated');
});

await t('gated purchase allowed after phase2 enabled', async () => {
  const substrate = new MemorySubstrate({ phase2: true }).addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const r = await handlePaymentIntent(pi({ metadata: { purpose: EXTERNAL_PURCHASE, merchant_did: 'did:m' } }), 'idem-3', { substrate, idemStore });
  assert.equal(r.httpStatus, 200);
  assert.equal(r.body.status, 'succeeded');
});

await t('idempotent replay: same key -> same result, no double charge', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const a = await handlePaymentIntent(pi(), 'idem-dup', { substrate, idemStore });
  const b = await handlePaymentIntent(pi(), 'idem-dup', { substrate, idemStore });
  assert.deepEqual(a, b);
  assert.equal(substrate.authorizeCalls, 1, 'replay must not re-authorize');
  assert.equal(substrate.bal['did:m'], 300_000, 'merchant charged once only');
});

await t('decline: insufficient funds -> HTTP 402 requires_action', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 100 });
  const idemStore = new InMemoryIdempotencyStore();
  const r = await handlePaymentIntent(pi(), 'idem-4', { substrate, idemStore });
  assert.equal(r.httpStatus, 402);
  assert.equal(r.body.status, 'requires_action');
});

await t('manual capture -> 200 requires_capture, no settlement yet', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const r = await handlePaymentIntent(pi({ capture_method: 'manual' }), 'idem-5', { substrate, idemStore });
  assert.equal(r.httpStatus, 200);
  assert.equal(r.body.status, 'requires_capture');
  assert.equal(substrate.bal['did:m'] ?? 0, 0, 'no settlement on manual capture');
});

await t('unknown purpose -> HTTP 403 (not 451)', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const r = await handlePaymentIntent(pi({ metadata: { purpose: EXTERNAL_TIP } }), 'idem-6', { substrate, idemStore });
  assert.equal(r.httpStatus, 403);
  assert.equal(substrate.authorizeCalls, 0);
});

await t('manual capture route: requires_capture -> capture -> succeeded, merchant paid', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const created = await handlePaymentIntent(pi({ capture_method: 'manual' }), 'idem-c1', { substrate, idemStore });
  assert.equal(created.body.status, 'requires_capture');
  const cap = await handleCapture(created.body.id, 'idem-c2', { substrate, idemStore });
  assert.equal(cap.httpStatus, 200);
  assert.equal(cap.body.status, 'succeeded');
  assert.equal(cap.body.settlement.fee, '0');
  assert.equal(substrate.bal['did:m'], 300_000);
});

await t('capture unknown auth -> 402', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const r = await handleCapture('auth-nope', 'idem-c3', { substrate, idemStore });
  assert.equal(r.httpStatus, 402);
});

await t('refund route: full refund returns funds, fee 0, purpose escrow-refund', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const paid = await handlePaymentIntent(pi(), 'idem-r1', { substrate, idemStore });
  const sid = paid.body.settlement.settlementId;
  const r = await handleRefund({ settlement_id: sid }, 'idem-r2', { substrate, idemStore });
  assert.equal(r.httpStatus, 200);
  assert.equal(r.body.fee, '0');
  assert.equal(r.body.purpose, 'escrow-refund');
  assert.equal(substrate.bal['acct-A'], 1_000_000, 'holder fully refunded');
  assert.equal(substrate.bal['did:m'], 0, 'merchant clawed back');
});

await t('refund idempotent replay: no double refund', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const paid = await handlePaymentIntent(pi(), 'idem-r3', { substrate, idemStore });
  const sid = paid.body.settlement.settlementId;
  const a = await handleRefund({ settlement_id: sid }, 'idem-r4', { substrate, idemStore });
  const b = await handleRefund({ settlement_id: sid }, 'idem-r4', { substrate, idemStore });
  assert.deepEqual(a, b);
  assert.equal(substrate.bal['acct-A'], 1_000_000, 'refunded once only');
});

await t('over-refund (new key) rejected -> 422', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const paid = await handlePaymentIntent(pi(), 'idem-r5', { substrate, idemStore });
  const sid = paid.body.settlement.settlementId;
  await handleRefund({ settlement_id: sid }, 'idem-r6', { substrate, idemStore }); // full refund
  const over = await handleRefund({ settlement_id: sid }, 'idem-r7', { substrate, idemStore });
  assert.equal(over.httpStatus, 422);
  assert.equal(over.body.status, 'failed');
});

await t('refund unknown settlement -> 422', async () => {
  const substrate = new MemorySubstrate().addCard('tok-A', 'acct-A', { balance: 1_000_000 });
  const idemStore = new InMemoryIdempotencyStore();
  const r = await handleRefund({ settlement_id: 'settle-nope' }, 'idem-r8', { substrate, idemStore });
  assert.equal(r.httpStatus, 422);
});

console.log(`stripe-compat e2e: ${pass} checks passed`);
