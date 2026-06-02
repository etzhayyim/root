// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Surface C — mobile NFC (Host Card Emulation) → com.etzhayyim.card.* (ADR-2605302000).
// The app emulates a contactless EMV card; our own TSP detokenizes. Raw PAN is never present.
// CVM = WebAuthn passkey (device biometric) = 3-D-Secure-equivalent. No platform-held key.

import type { CardAuthorizeInput } from '../common/types.js';
import { nfcTapToAuthorize as _nfcTapToAuthorize } from './handler.js';

/** A contactless tap as surfaced by the HCE service after detokenization. */
export interface NfcTap {
  cardToken: string; // network token from self-TSP detokenize (NOT a PAN)
  amountUsdc: number;
  merchantDid: string;
  emvCryptogram: string;
  /** WebAuthn passkey assertion captured at tap time (device biometric CVM). */
  passkeyAssertion: string;
  stan: string; // correlation id
}

/** Mapping lives in ./handler.js (single runnable SoT); this is the typed surface. */
export const nfcTapToAuthorize = _nfcTapToAuthorize as (
  tap: NfcTap,
  purpose?: string,
) => CardAuthorizeInput;
