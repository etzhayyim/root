// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Surface A — Stripe-shaped REST types + typed adapter (ADR-2605302000). Interoperable open
// re-implementation of common card-API shapes; NOT a clone of any vendor. Merchants change
// baseURL only. Fee is always 0. The request FLOW lives in ./handler.js (single runnable SoT,
// node-tested); this file is the typed wrapper.

import type { WarifuSubstrate as Substrate } from '../common/sdk.js';
import { handlePaymentIntent, handleCapture, handleRefund } from './handler.js';

/** Stripe-shaped PaymentIntent create body (subset we honor). */
export interface PaymentIntentCreate {
  amount: number; // USDC minor units
  currency: 'usdc';
  payment_method: string; // wpm_... -> cardToken
  capture_method?: 'automatic' | 'manual';
  metadata?: { purpose?: string; merchant_did?: string };
}

export interface PaymentIntentSettlement {
  chain: 'base';
  tx?: string;
  fee: '0';
  finality: 'T+0';
}

export interface PaymentIntentResponse {
  id: string;
  status: 'succeeded' | 'requires_capture' | 'requires_action';
  amount: number;
  settlement?: PaymentIntentSettlement;
  /** Present when the purpose is constitutionally gated (HTTP 451) or otherwise refused. */
  error?: { type: string; message: string };
}

/** Idempotency store handle (see ../common/idempotency.js). */
export interface IdempotencyStore {
  get(key: string): unknown;
  begin(key: string): void;
  complete(key: string, result: unknown): void;
  fail(key: string): void;
}

export interface PaymentIntentDeps {
  substrate: Substrate;
  idemStore: IdempotencyStore;
}

/** Result including the HTTP status the route should emit (451 on gate, 402 on decline, …). */
export interface PaymentIntentResult {
  httpStatus: number;
  body: PaymentIntentResponse;
}

/**
 * Translate + execute a Stripe-shaped PaymentIntent. Delegates the flow to handler.js so there is
 * exactly one implementation (idempotency → purpose-gate → authorize → settle).
 */
export async function createPaymentIntent(
  body: PaymentIntentCreate,
  idempotencyKey: string,
  deps: PaymentIntentDeps,
  passkeyAssertion?: string,
): Promise<PaymentIntentResult> {
  return handlePaymentIntent(
    { ...body, passkey: passkeyAssertion },
    idempotencyKey,
    deps,
  ) as Promise<PaymentIntentResult>;
}

/** Capture a manually-authorized PaymentIntent (POST /v1/payment_intents/:id/capture). */
export async function capturePaymentIntent(
  authId: string,
  idempotencyKey: string,
  deps: PaymentIntentDeps,
): Promise<PaymentIntentResult> {
  return handleCapture(authId, idempotencyKey, deps) as Promise<PaymentIntentResult>;
}

export interface RefundCreate {
  settlement_id: string;
  amount?: number; // omit for full refund
}

export interface RefundResponse {
  id?: string;
  status: 'succeeded' | 'failed';
  amount?: number;
  purpose?: 'escrow-refund';
  tx?: string;
  fee?: '0';
  error?: { type: string; message: string };
}

export interface RefundResult {
  httpStatus: number;
  body: RefundResponse;
}

/** Refund a settlement (POST /v1/refunds). Purpose is always escrow-refund; fee 0. */
export async function createRefund(
  body: RefundCreate,
  idempotencyKey: string,
  deps: PaymentIntentDeps,
): Promise<RefundResult> {
  return handleRefund(body, idempotencyKey, deps) as Promise<RefundResult>;
}
