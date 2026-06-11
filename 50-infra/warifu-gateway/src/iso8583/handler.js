// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Surface B flow — ISO 8583 0100 → authorize→settle → 0110 (ADR-2605302000). Runnable SoT; the
// typed adapter (translate.ts) imports the mapping from here. Idempotency keyed by DE11 STAN.
// Fee 0; no key held.

import { withIdempotency } from '../common/idempotency.js';
import { authorizeAndSettle } from '../common/settle-flow.js';
import { toUsdcMinor, fundingFromProcessingCode, DE39 } from '../common/iso8583-codec.js';

/**
 * Map a 0100 auth request to a substrate-native CardAuthorizeInput.
 * @param {object} msg  {de2_pan, de3_processingCode, de4_amount, de11_stan, de42_merchantId, de55_emv?}
 * @param {(merchantId:string)=>string} merchantDidLookup
 * @param {string} [purpose='internal-purchase']
 */
export function iso8583ToAuthorize(msg, merchantDidLookup, purpose = 'internal-purchase') {
  return {
    cardToken: msg.de2_pan,
    amountUsdc: toUsdcMinor(msg.de4_amount),
    funding: fundingFromProcessingCode(msg.de3_processingCode),
    purpose,
    merchantDid: merchantDidLookup(msg.de42_merchantId),
    idempotencyKey: msg.de11_stan,
    surface: 'iso8583',
    threeDS: msg.de55_emv,
  };
}

/**
 * Handle a 0100 authorization (auto-settles on approve). Returns a 0110 response.
 * @returns {Promise<{mti:'0110', de39_responseCode:string, authId?:string, settlementId?:string}>}
 */
export async function handleIso8583Auth(msg, { substrate, idemStore }, merchantDidLookup, purpose = 'internal-purchase') {
  return withIdempotency(idemStore, msg.de11_stan, async () => {
    const authInput = iso8583ToAuthorize(msg, merchantDidLookup, purpose);
    const r = await authorizeAndSettle(authInput, { substrate }, { autoCapture: true });

    let de39;
    if (r.gate === 'gated') de39 = DE39.GATED; // 57 transaction not permitted (Phase 2 off)
    else if (r.gate === 'denied') de39 = DE39.INVALID; // 12 invalid (unknown purpose)
    else if (r.decision === 'approve' && r.settled) de39 = DE39.APPROVE; // 00
    else de39 = DE39.DECLINE; // 05 do-not-honor

    return { mti: '0110', de39_responseCode: de39, authId: r.authId, settlementId: r.settlementId };
  });
}
