// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Payment-purpose allow-list — the SINGLE source of truth shared by all 3 compat surfaces
// (Stripe-REST / ISO 8583 / NFC). MUST stay in lockstep with the other two enforcement points:
//   - Solidity:  50-infra/warifu-contracts/src/SettlementRouter.sol  (_checkPurpose)
//   - Python:    orgs/etzhayyim/com-etzhayyim-warifu/cells/authorize.py                 (AuthorizeCell._purpose_ok)
// ADR-2605302000 / ADR-2605192115 §3.
//
// Plain ESM (JSDoc-typed) so it is BOTH directly runnable by node (tests) AND importable by the
// TypeScript translators. No substrate imports here — pure policy.

/** Phase 1 charter-clean purposes (SBT↔SBT carve-out + escrow-refund). */
export const PHASE1_PURPOSES = Object.freeze([
  'internal-purchase',
  'internal-subscription',
  'internal-promo',
  'escrow-refund',
]);

/** External commercial purposes — gated until a Council Lv7+ amendment of ADR-2605192115. */
export const PHASE2_GATED_PURPOSES = Object.freeze(['purchase', 'subscription']);

/**
 * @typedef {'phase1'|'gated'|'denied'} PurposeVerdict
 * - phase1  : permitted now (closed-loop)
 * - gated   : a known external purpose, blocked until phase2Enabled (Lv7+ + vendor MoR)
 * - denied  : unknown / prohibited purpose
 */

/**
 * @param {string} purpose
 * @param {boolean} [phase2Enabled=false]
 * @returns {PurposeVerdict}
 */
export function evaluatePurpose(purpose, phase2Enabled = false) {
  if (PHASE1_PURPOSES.includes(purpose)) return 'phase1';
  if (PHASE2_GATED_PURPOSES.includes(purpose)) return phase2Enabled ? 'phase1' : 'gated';
  return 'denied';
}

/** True iff the purpose may settle right now under the given phase flag. */
export function isPurposeAllowed(purpose, phase2Enabled = false) {
  return evaluatePurpose(purpose, phase2Enabled) === 'phase1';
}
