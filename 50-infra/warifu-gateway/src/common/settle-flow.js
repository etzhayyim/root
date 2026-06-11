// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Shared authorize→settle core for ALL three surfaces (ADR-2605302000). One implementation of the
// fail-closed purpose gate + authorize + (optional) settle, so Stripe-REST / ISO 8583 / NFC cannot
// drift apart. Idempotency is applied by the CALLER (each surface keys it differently:
// Idempotency-Key / DE11 STAN / NFC tap correlation), so this function is NOT itself wrapped.
//
// Fee is always 0; no key held. Returns a surface-neutral verdict the handlers shape per protocol.

import { evaluatePurpose } from './purpose.js';

/**
 * @param {object} authInput  CardAuthorizeInput (cardToken, amountUsdc, funding, purpose,
 *   merchantDid, idempotencyKey, surface, threeDS?)
 * @param {{substrate:object}} deps
 * @param {{autoCapture?:boolean}} [opts]
 * @returns {Promise<{
 *   gate:'phase1'|'gated'|'denied',
 *   decision?:'approve'|'decline',
 *   authId?:string, reason?:string,
 *   captured?:boolean, settled?:boolean, tx?:string, settlementId?:string
 * }>}
 */
export async function authorizeAndSettle(authInput, { substrate }, { autoCapture = true } = {}) {
  const phase2 = await substrate.phase2Enabled();
  const verdict = evaluatePurpose(authInput.purpose, phase2);

  // Fail-closed BEFORE the substrate is touched.
  if (verdict !== 'phase1') return { gate: verdict };

  const auth = await substrate.authorize(authInput);
  if (auth.decision !== 'approve' || !auth.authId) {
    return { gate: 'phase1', decision: auth.decision ?? 'decline', reason: auth.reason };
  }

  if (!autoCapture) {
    return { gate: 'phase1', decision: 'approve', authId: auth.authId, captured: false };
  }

  const s = await substrate.settle({ authId: auth.authId, idempotencyKey: authInput.idempotencyKey });
  return {
    gate: 'phase1',
    decision: 'approve',
    authId: auth.authId,
    captured: true,
    settled: s.settled,
    tx: s.tx,
    settlementId: s.settlementId,
  };
}
