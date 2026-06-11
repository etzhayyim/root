// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Surface C flow — mobile NFC (HCE) tap → authorize→settle (ADR-2605302000). Runnable SoT; the
// typed adapter (translate.ts) imports the mapping from here. Idempotency keyed by tap STAN.
// CVM = WebAuthn passkey (device biometric). Fee 0; no key held; no raw PAN.

import { withIdempotency } from '../common/idempotency.js';
import { authorizeAndSettle } from '../common/settle-flow.js';

/**
 * Map a detokenized HCE tap to a substrate-native CardAuthorizeInput.
 * @param {object} tap  {cardToken, amountUsdc, merchantDid, emvCryptogram, passkeyAssertion, stan}
 * @param {string} [purpose='internal-purchase']
 */
export function nfcTapToAuthorize(tap, purpose = 'internal-purchase') {
  return {
    cardToken: tap.cardToken, // network token from self-TSP detokenize (NOT a PAN)
    amountUsdc: tap.amountUsdc,
    funding: 'debit',
    purpose,
    merchantDid: tap.merchantDid,
    idempotencyKey: tap.stan,
    surface: 'nfc',
    threeDS: tap.passkeyAssertion,
  };
}

/**
 * Handle an NFC tap (auto-settles on approve).
 * @returns {Promise<{approved:boolean, gate:string, decision?:string, tx?:string, settlementId?:string}>}
 */
export async function handleNfcTap(tap, { substrate, idemStore }, purpose = 'internal-purchase') {
  return withIdempotency(idemStore, tap.stan, async () => {
    const r = await authorizeAndSettle(nfcTapToAuthorize(tap, purpose), { substrate }, { autoCapture: true });
    return {
      approved: r.gate === 'phase1' && r.decision === 'approve' && !!r.settled,
      gate: r.gate,
      decision: r.decision,
      tx: r.tx,
      settlementId: r.settlementId,
    };
  });
}
