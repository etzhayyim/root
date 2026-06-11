// SPDX-License-Identifier: Apache-2.0
// Runnable with: node src/common/purpose.test.mjs   (no test framework / no deps)
import assert from 'node:assert/strict';
import { evaluatePurpose, isPurposeAllowed } from './purpose.js';

let pass = 0;
const t = (name, fn) => { fn(); pass++; console.log(`  ok ${name}`); };

t('phase1 purposes allowed regardless of phase flag', () => {
  for (const p of ['internal-purchase', 'internal-subscription', 'internal-promo', 'escrow-refund']) {
    assert.equal(evaluatePurpose(p, false), 'phase1');
    assert.equal(evaluatePurpose(p, true), 'phase1');
  }
});

t('external purchase/subscription GATED before phase2', () => {
  assert.equal(evaluatePurpose('purchase', false), 'gated');
  assert.equal(evaluatePurpose('subscription', false), 'gated');
  assert.equal(isPurposeAllowed('purchase', false), false);
});

t('external purchase/subscription allowed only after phase2', () => {
  assert.equal(evaluatePurpose('purchase', true), 'phase1');
  assert.equal(isPurposeAllowed('subscription', true), true);
});

t('unknown / prohibited purposes denied even with phase2', () => {
  for (const p of ['tip', 'donation-external', 'cashout', '']) {
    assert.equal(evaluatePurpose(p, true), 'denied');
  }
});

console.log(`purpose-gate: ${pass} checks passed`);
