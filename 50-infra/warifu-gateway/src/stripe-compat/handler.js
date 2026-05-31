// SPDX-License-Identifier: Apache-2.0
// etzhayyim Charter Compliance Rider v2.0 applies (see /CHARTER-RIDER.md).
//
// Surface A request flow — the runnable SoT for POST /v1/payment_intents (ADR-2605302000).
// Wires idempotency → purpose-gate (HTTP 451 when gated) → authorize → settle, returning a
// Stripe-shaped body. Fee is always 0. The .ts route/translator delegate here so there is ONE
// flow implementation (no drift). The handler holds no key; cardholder auth rides on `passkey`.

import { withIdempotency } from '../common/idempotency.js';
import { authorizeAndSettle } from '../common/settle-flow.js';

const GATE_MESSAGE =
  'purpose constitutionally gated — Phase 2 external acceptance requires a Council Lv7+ ' +
  'amendment (ADR-2605192115) + vendor merchant-of-record (ADR-2605301036)';

/**
 * @param {object} body  Stripe-shaped PaymentIntent create body ({amount, currency,
 *   payment_method, capture_method?, metadata?:{purpose?,merchant_did?}, passkey?})
 * @param {string} idempotencyKey
 * @param {{substrate:object, idemStore:object}} deps
 * @returns {Promise<{httpStatus:number, body:object}>}
 */
export async function handlePaymentIntent(body, idempotencyKey, { substrate, idemStore }) {
  return withIdempotency(idemStore, idempotencyKey, async () => {
    const purpose = body?.metadata?.purpose ?? 'internal-purchase';
    const authInput = {
      cardToken: body.payment_method,
      amountUsdc: body.amount,
      funding: 'debit', // credit is a card attribute resolved substrate-side
      purpose,
      merchantDid: body?.metadata?.merchant_did ?? '',
      idempotencyKey,
      surface: 'rest',
      threeDS: body.passkey,
    };
    const r = await authorizeAndSettle(authInput, { substrate }, {
      autoCapture: body.capture_method !== 'manual',
    });

    // Fail-closed: gated / prohibited purpose never touched the substrate.
    if (r.gate !== 'phase1') {
      const gated = r.gate === 'gated';
      return {
        httpStatus: gated ? 451 : 403, // 451 Unavailable For Legal Reasons / 403 forbidden
        body: {
          id: 'wpi_pending',
          status: 'requires_action',
          amount: body.amount,
          error: {
            type: gated ? 'unavailable_for_legal_reasons' : 'invalid_request_error',
            message: gated ? GATE_MESSAGE : `purpose '${purpose}' not permitted`,
          },
        },
      };
    }

    if (r.decision !== 'approve') {
      return {
        httpStatus: 402, // Payment Required
        body: { id: 'wpi_pending', status: 'requires_action', amount: body.amount },
      };
    }

    if (r.captured === false) {
      return {
        httpStatus: 200,
        body: { id: r.authId, status: 'requires_capture', amount: body.amount },
      };
    }

    return {
      httpStatus: 200,
      body: {
        id: r.authId,
        status: r.settled ? 'succeeded' : 'requires_action',
        amount: body.amount,
        settlement: r.settled
          ? { chain: 'base', settlementId: r.settlementId, tx: r.tx, fee: '0', finality: 'T+0' }
          : undefined,
      },
    };
  });
}

/**
 * Capture a manually-authorized PaymentIntent (POST /v1/payment_intents/:id/capture).
 * Idempotent; settles the held auth. Fee 0.
 * @param {string} authId
 * @param {string} idempotencyKey
 * @param {{substrate:object, idemStore:object}} deps
 * @returns {Promise<{httpStatus:number, body:object}>}
 */
export async function handleCapture(authId, idempotencyKey, { substrate, idemStore }) {
  return withIdempotency(idemStore, idempotencyKey, async () => {
    const s = await substrate.settle({ authId, idempotencyKey });
    if (!s.settled) {
      return { httpStatus: 402, body: { id: authId, status: 'requires_action' } };
    }
    return {
      httpStatus: 200,
      body: {
        id: authId,
        status: 'succeeded',
        settlement: { chain: 'base', settlementId: s.settlementId, tx: s.tx, fee: '0', finality: 'T+0' },
      },
    };
  });
}

/**
 * Refund a settlement (POST /v1/refunds). Purpose is always escrow-refund; idempotent; fee 0.
 * @param {object} body  {settlement_id, amount?}
 * @param {string} idempotencyKey
 * @param {{substrate:object, idemStore:object}} deps
 * @returns {Promise<{httpStatus:number, body:object}>}
 */
export async function handleRefund(body, idempotencyKey, { substrate, idemStore }) {
  return withIdempotency(idemStore, idempotencyKey, async () => {
    const r = await substrate.refund({
      settlementId: body.settlement_id,
      amountUsdc: body.amount,
    });
    if (!r.refunded) {
      return {
        httpStatus: 422,
        body: { status: 'failed', error: { type: 'refund_error', message: r.reason ?? 'refund failed' } },
      };
    }
    return {
      httpStatus: 200,
      body: {
        id: r.refundId,
        status: 'succeeded',
        amount: r.amountUsdc,
        purpose: 'escrow-refund',
        tx: r.tx,
        fee: '0',
      },
    };
  });
}
