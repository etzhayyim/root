// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Surface B — ISO 8583 (card-present / EMV terminal) → com.etzhayyim.card.* (ADR-2605302000).
// R0 scope: message/field map only (see ../iso8583-map.md). Physical terminal acceptance needs a
// BIN/acquirer membership and is deferred to R2+.
//
// Pure codec lives in ../common/iso8583-codec.js (single SoT, node-tested). This file is the typed
// adapter that shapes substrate-native CardAuthorizeInput from terminal messages.

import type { CardAuthorizeInput, Decision } from '../common/types.js';
import { DE39, toUsdcMinor, decisionToDe39 } from '../common/iso8583-codec.js';
import { iso8583ToAuthorize as _iso8583ToAuthorize } from './handler.js';

export { DE39, toUsdcMinor };

/** Subset of ISO 8583 data elements the gateway consumes for a 0100 authorization request. */
export interface Iso8583AuthRequest {
  mti: '0100';
  de2_pan: string; // network token (no raw PAN) -> cardToken
  de3_processingCode: string; // e.g. '000000' purchase debit, '003000' balance inquiry
  de4_amount: string; // minor units in terminal currency
  de11_stan: string; // -> idempotencyKey correlation
  de41_terminalId?: string;
  de42_merchantId: string; // -> resolve merchantDid
  de55_emv?: string; // EMV/ICC cryptogram (verified upstream)
}

export interface Iso8583AuthResponse {
  mti: '0110';
  de39_responseCode: string; // 00 / 05 / 57 / 12
}

/**
 * Translate a 0100 auth request into a substrate-native CardAuthorizeInput.
 * Mapping lives in ./handler.js (single runnable SoT); this is the typed surface.
 */
export const iso8583ToAuthorize = _iso8583ToAuthorize as (
  msg: Iso8583AuthRequest,
  merchantDidLookup: (merchantId: string) => string,
  purpose?: string,
) => CardAuthorizeInput;

/** Map a substrate authorize decision back to a 0110 response code. */
export function decisionToIso8583(decision: Decision, denied = false): Iso8583AuthResponse {
  return { mti: '0110', de39_responseCode: decisionToDe39(decision, denied) };
}
