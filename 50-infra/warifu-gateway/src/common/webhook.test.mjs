// SPDX-License-Identifier: Apache-2.0
// Runnable: node src/common/webhook.test.mjs   (no deps)
import assert from 'node:assert/strict';
import { buildSettlementEvent, signPayload, verifySignature } from './webhook.js';

let pass = 0;
const t = (name, fn) => { fn(); pass++; console.log(`  ok ${name}`); };

const TS = 1_700_000_000;            // fixed timestamp (deterministic)
const NOW = TS * 1000;
const SECRET = 'whsec_merchant_abc';
const event = buildSettlementEvent({ settlementId: 'settle-1', amountUsdc: 300_000, tx: '0xabc' });
const body = JSON.stringify(event);

t('event carries fee 0 + on-chain tx + base chain', () => {
  assert.equal(event.type, 'card.settled');
  assert.equal(event.data.fee, '0');
  assert.equal(event.data.tx, '0xabc');
  assert.equal(event.data.chain, 'base');
});

t('sign then verify round-trips true', () => {
  const sig = signPayload(body, SECRET, TS);
  assert.equal(verifySignature(body, sig, SECRET, { nowSec: TS }), true);
});

t('tampered body fails', () => {
  const sig = signPayload(body, SECRET, TS);
  assert.equal(verifySignature(body + ' ', sig, SECRET, { nowSec: TS }), false);
});

t('wrong secret fails', () => {
  const sig = signPayload(body, SECRET, TS);
  assert.equal(verifySignature(body, sig, 'whsec_wrong', { nowSec: TS }), false);
});

t('expired timestamp (outside tolerance) fails — replay protection', () => {
  const sig = signPayload(body, SECRET, TS);
  assert.equal(verifySignature(body, sig, SECRET, { nowSec: TS + 301 }), false);
  assert.equal(verifySignature(body, sig, SECRET, { nowSec: TS + 299 }), true);
});

t('malformed / missing header fails', () => {
  assert.equal(verifySignature(body, '', SECRET, { nowSec: TS }), false);
  assert.equal(verifySignature(body, 'garbage', SECRET, { nowSec: TS }), false);
  assert.equal(verifySignature(body, 't=abc,v1=zz', SECRET, { nowSec: TS }), false);
});

t('signature mismatch length / bad hex fails safely', () => {
  assert.equal(verifySignature(body, `t=${TS},v1=00`, SECRET, { nowSec: TS }), false);
});

console.log(`webhook: ${pass} checks passed`);
