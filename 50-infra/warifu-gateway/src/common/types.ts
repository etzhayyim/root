// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Shared types for the warifu compat gateway. The substrate-native shapes mirror the
// `com.etzhayyim.card.*` lexicons (orgs/etzhayyim/com-etzhayyim-warifu/wire/lex/). Fee is always 0 (決済手数料ゼロ).

export type Funding = 'debit' | 'credit';
export type Surface = 'rest' | 'iso8583' | 'nfc';
export type Decision = 'approve' | 'decline' | 'gated';

/** Substrate-native authorize request — what every surface translates *into*. */
export interface CardAuthorizeInput {
  cardToken: string; // network token; no raw PAN (self TSP)
  amountUsdc: number; // USDC minor units (6dp)
  funding: Funding;
  purpose: string; // validated against the shared purpose allow-list
  merchantDid: string;
  idempotencyKey: string;
  surface: Surface;
  /** WebAuthn passkey assertion (3-D-Secure-equivalent). The gateway NEVER holds a key. */
  threeDS?: string;
}

export interface CardAuthorizeOutput {
  decision: Decision;
  authId?: string;
  reason?: string;
  feeUsdc: 0; // invariant
}

export interface CardSettleInput {
  authId: string;
  amountUsdc?: number;
  idempotencyKey?: string;
}

export interface CardSettleOutput {
  settled: boolean;
  settlementId?: string;
  tx?: string;
  feeUsdc: 0;
  finality: 'T+0';
}

export interface CardRefundInput {
  settlementId: string;
  amountUsdc?: number;
  idempotencyKey?: string;
  reason?: string;
}

export interface CardRefundOutput {
  refunded: boolean;
  refundId?: string;
  amountUsdc?: number;
  tx?: string;
  feeUsdc: 0;
}
