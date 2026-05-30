// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Merchant webhook signing/verification for warifu settlement events (ADR-2605302000).
// Stripe-style `t=<unix>,v1=<hmac-sha256>` header over `${t}.${rawBody}`, with a timestamp
// tolerance window (replay protection) and constant-time comparison.
//
// Charter note: the HMAC key is a PER-MERCHANT shared secret (`whsec_…`) used so the merchant can
// verify OUR notifications — NOT a platform-held private key or master credential signing on a
// user's behalf (ADR-2605231525 is about the latter). Belt-and-suspenders: every event also
// carries the on-chain settlement `tx`, so a merchant can verify trustlessly against Base L2
// without trusting the gateway at all. Fee is always '0'.

import { createHmac, timingSafeEqual } from 'node:crypto';

/** Canonical settlement event (what merchants receive). */
export function buildSettlementEvent(settlement, createdSec) {
  return {
    id: `evt_${settlement.settlementId}`,
    type: 'card.settled',
    ...(createdSec !== undefined ? { created: createdSec } : {}),
    data: {
      object: 'settlement',
      id: settlement.settlementId,
      amount: settlement.amountUsdc,
      currency: 'usdc',
      fee: '0', // 決済手数料ゼロ invariant
      chain: 'base',
      tx: settlement.tx, // on-chain proof — merchant can verify independently
    },
  };
}

/** Sign a raw JSON body. Returns the `Warifu-Signature` header value. */
export function signPayload(rawBody, secret, timestampSec) {
  const ts = String(timestampSec);
  const mac = createHmac('sha256', secret).update(`${ts}.${rawBody}`).digest('hex');
  return `t=${ts},v1=${mac}`;
}

function parseHeader(header) {
  const out = {};
  for (const part of String(header).split(',')) {
    const i = part.indexOf('=');
    if (i > 0) out[part.slice(0, i).trim()] = part.slice(i + 1).trim();
  }
  return out;
}

/**
 * Verify a signature header against the raw body.
 * @param {string} rawBody
 * @param {string} header  value of Warifu-Signature
 * @param {string} secret  per-merchant whsec
 * @param {{toleranceSec?:number, nowSec?:number}} [opts]
 * @returns {boolean}
 */
export function verifySignature(rawBody, header, secret, opts = {}) {
  const toleranceSec = opts.toleranceSec ?? 300;
  const nowSec = opts.nowSec ?? Math.floor(Date.now() / 1000);
  const { t, v1 } = parseHeader(header || '');
  if (!t || !v1 || !/^\d+$/.test(t)) return false;

  // replay window
  if (Math.abs(nowSec - Number(t)) > toleranceSec) return false;

  const expected = createHmac('sha256', secret).update(`${t}.${rawBody}`).digest('hex');
  const a = Buffer.from(v1, 'hex');
  const b = Buffer.from(expected, 'hex');
  if (a.length !== b.length) return false; // also guards malformed/odd-length hex
  return timingSafeEqual(a, b);
}
