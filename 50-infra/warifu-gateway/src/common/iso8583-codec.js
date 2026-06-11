// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// ISO 8583 codec — the pure, runnable core of Surface B (ADR-2605302000 / see ../iso8583-map.md).
// Kept as plain ESM so it is node-testable AND importable by iso8583/translate.ts (single SoT).

/** DE39 response codes used by warifu. */
export const DE39 = Object.freeze({
  APPROVE: '00',
  DECLINE: '05', // do-not-honor (insufficient funds/credit)
  GATED: '57', // transaction not permitted (purpose gated — Phase 2 not enabled)
  INVALID: '12', // invalid transaction (unknown purpose)
});

/**
 * Normalise a terminal minor-unit amount (DE4) to USDC 6dp minor units.
 * e.g. "1200" cents (exponent 2) -> 12_000_000 USDC minor.
 * @param {string|number} amountField
 * @param {number} [terminalExponent=2]
 * @returns {number} USDC minor units, or NaN if the input is not finite
 */
export function toUsdcMinor(amountField, terminalExponent = 2) {
  const n = Number(amountField);
  if (!Number.isFinite(n)) return NaN;
  return Math.round(n * 10 ** (6 - terminalExponent));
}

/**
 * Processing-code (DE3) -> funding. R0: goods/services purchase maps to debit; credit vs debit is
 * resolved substrate-side from the card attribute, so this is intentionally conservative.
 * @param {string} de3
 * @returns {'debit'|'credit'}
 */
export function fundingFromProcessingCode(de3) {
  return de3 && de3.startsWith('00') ? 'debit' : 'debit';
}

/**
 * Map a substrate authorize decision to a DE39 response code.
 * @param {'approve'|'decline'|'gated'} decision
 * @param {boolean} [denied=false] — true when the decline was an unknown/prohibited purpose
 * @returns {string} DE39 code
 */
export function decisionToDe39(decision, denied = false) {
  if (decision === 'approve') return DE39.APPROVE;
  if (decision === 'gated') return DE39.GATED;
  if (denied) return DE39.INVALID;
  return DE39.DECLINE;
}
