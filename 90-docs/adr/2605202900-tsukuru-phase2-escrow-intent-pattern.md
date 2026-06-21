---
id: adr-2605202900-tsukuru-phase2-escrow-intent-pattern
title: "ADR-2605202900: tsukuru Phase 2 — deferred-payment escrow_intent pattern (SDK v0.1 reference impl)"
status: proposed
doc_type: adr
topic: tsukuru-phase2-escrow-intent-pattern
authoritative: true
last_verified: 2026-05-20
priority: 6.8
axis: payment
weight: 0.68
priority_note: "Phase 2 pattern doc accompanying the first tsukuru kotoba reference impl (productionOrder.create + cancel). Active for SDK v0.1.x. Superseded when SDK v0.2 ships escrowOpen()/escrowRelease() and tsukuru migrates to on-chain Safe escrow."
authoritative_for:
  - tsukuru Phase 2 payment pattern (record-only escrow intent)
  - Stripe Issuing cancelCard → record-state-machine refund mapping
  - tsukuru productionOrder.{create,cancel} lexicon shape (tightened in this PR)
depends_on:
  - adr-2605172000-etzhayyim-kotoba-substrate
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605202800-tsukuru-etzhayyim-business-model-change
related:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
supersedes: []
superseded_by: []
---

# ADR-2605202900: tsukuru Phase 2 — deferred-payment escrow_intent pattern

**Status**: proposed
**Date**: 2026-05-20
**Deciders**: Jun Kawasaki

# Context

[ADR-2605202800](./2605202800-tsukuru-etzhayyim-business-model-change.md) commits tsukuru to a Stripe Issuing → ERC-4337 + USDC migration as part of the full-move to etzhayyim. Phase 2 needs a concrete payment pattern that:

1. **Replaces Stripe Issuing `chargeCustomer` + `cancelCard`** semantics.
2. **Works with the current [@etzhayyim/sdk](../../20-actors/etzhayyim-sdk/) v0.1.x** which has working `pay()` (EOA USDC.transfer + `payment.sent` record) but throws for `escrowOpen()` / `escrowRelease()` ("v0.2+" per `pay.ts:307-321`).
3. **Preserves the cancellation flow** — buyers must be able to cancel pending orders without losing funds.
4. **Avoids on-chain settlement before delivery** — manufacturer hasn't shipped yet, so an irreversible USDC.transfer at order creation would be premature.

The Safe 2-of-3 escrow contract from `payment.escrowOpened.json` lexicon (Phase 3 wave 4) is the long-term target, but cannot be deployed today because the SDK contract layer is incomplete.

# Decision

**Use a record-only deferred-payment intent pattern.** No on-chain USDC moves until delivery confirmation. State transitions are encoded as AT Protocol records and enforced by application logic + firehose audit, not by a Safe contract.

## State machine

```
   ┌────────────────────────────────┐
   │ createProductionOrder()        │
   │   payment.method == "escrow_   │
   │   intent"                      │
   └─────────────┬──────────────────┘
                 │
                 ▼
   ┌────────────────────────────────────────┐
   │ openIntent() — escrow.ts               │
   │   write com.etzhayyim.apps.payment.          │
   │     escrowOpened                       │
   │   • safeAddress = 0x0...0 placeholder  │
   │   • arbiter     = 0x0...0 placeholder  │
   │   • dueDate     = now + 60 days        │
   │   NO on-chain tx                       │
   └─────────────┬──────────────────────────┘
                 │
                 ▼
   ┌────────────────────────────────┐
   │ productionOrder.status =       │
   │   "pending"                    │
   │ + escrowIntentUri              │
   └─────────────┬──────────────────┘
                 │
       ┌─────────┴─────────┐
       │                   │
       ▼                   ▼
   ┌──────────────┐   ┌────────────────────────┐
   │ DELIVERY     │   │ CANCEL                 │
   │ (next PR)    │   │  (this PR's cancel)    │
   │              │   │                        │
   │ e.pay()      │   │ refundIntent()         │
   │ USDC.transfer│   │   write payment.       │
   │ writes       │   │     escrowRefunded     │
   │   payment.   │   │   NO on-chain tx       │
   │   sent       │   │                        │
   └──────┬───────┘   └─────────┬──────────────┘
          │                     │
          ▼                     ▼
   ┌──────────────┐   ┌──────────────┐
   │ status =     │   │ status =     │
   │ "delivered"  │   │ "cancelled"  │
   │ paymentSent  │   │ escrowRefund │
   │   Uri set    │   │   Uri set    │
   └──────────────┘   └──────────────┘
```

## Why "intent record" instead of just "no escrow"

A naive alternative would be: no escrow at order create, then `e.pay()` at delivery. Why bother with an intent record?

1. **Cap commitment.** The intent locks the buyer to a specific amount + recipient + due date. Without it, the buyer could disappear at delivery time and the manufacturer's labor is unpaid.
2. **Arbiter slot.** The `arbiter` field is the future hook for Safe 2-of-3 on-chain escrow. Recording it as a placeholder today means Phase 2b migration is a single SDK upgrade, not a schema change.
3. **Audit trail.** Buyers and regulators can see funds were committed at order creation, even though they haven't moved yet. This matches Stripe Issuing's "authorized but not captured" semantics.
4. **Cancellation explicitness.** A cancellation event without a prior intent is meaningless. With the intent → refund record pair, the AT firehose carries a complete state machine.

## Why no on-chain tx at order creation

Three reasons:

1. **SDK doesn't support escrow yet.** `escrowOpen()` throws — we'd need to deploy a Safe contract from app code (forbidden per `pay.ts:11` — "the ONLY seam where viem writeContract for value transfer is allowed").
2. **Avoid premature commitment.** USDC.transfer at order creation is irreversible. If the manufacturer fails to deliver, the buyer's funds are gone and reclaim requires the manufacturer's cooperation (which won't come if they're a bad actor).
3. **Match Stripe Issuing UX.** Stripe Issuing's `cardAuthorization` flow is also "no money moves yet" — it locks an amount, captures at fulfillment. The intent record gives the same shape.

## Why on-chain tx at delivery (not at acceptance / shipment)

Picking the trigger:

- **At acceptance**: too early — manufacturer might not be able to actually fulfill.
- **At shipment**: still early — package can be lost in transit.
- **At delivery + quality_inspection.passed** (CHOSEN): manufacturer demonstrated full performance + buyer signed off.

This aligns with B2B norms (manufacturers regularly get paid Net-30 after delivery + invoice approval).

## Tightened lexicon schemas

Two lexicons updated from `x-bootstrap: true` auto-generated stubs to proper schemas in the same PR as this ADR:

### `com.etzhayyim.apps.tsukuru.productionOrder.createProductionOrder`

Old (bootstrap):
```json
"manufacturer_did": { "type": "integer" }
"customer_id": { "type": "integer" }
"priority": { "type": "string" }
```

New:
```json
"manufacturerDid": { "type": "string", "format": "did" }
"customerDid":     { "type": "string", "format": "did" }
"priority":        { "type": "string", "enum": ["low","normal","high","urgent"] }
"payment": {
  "method": { "enum": ["escrow_intent", "direct_pay"] },
  "amountUsdcMicros": { "type": "integer", "minimum": 1 },
  ...
}
```

Also adds `escrowIntentUri`, `estimatedCompletion`, etc. to the output schema.

### `com.etzhayyim.apps.tsukuru.productionOrder.cancelProductionOrder`

Old (bootstrap):
```json
"production_order_id": { "type": "integer" }
```

New:
```json
"productionOrderUri": { "type": "string", "format": "at-uri" }
"reason":             { "type": "string", "maxLength": 1000 }
"cancelledByDid":     { "type": "string", "format": "did" }
```

Output:
```json
"status": { "enum": ["cancelled", "cannotCancel"] }
"escrowRefundUri": { "type": "string", "format": "at-uri" }
"cancellableStatuses": { "type": "array", ... }
```

These lexicons are simultaneously SSoT in vendor `00-contracts/lexicons/com/etzhayyim/apps/tsukuru/productionOrder/` and etzhayyim `00-contracts/lexicons/com/etzhayyim/apps/tsukuru/productionOrder/`. The PR updates the etzhayyim copy; vendor copy will sync at next bundle regen (lexicon Phase 6 cleanup tracking).

# Consequences

## 正の効果

- **Cancellation works.** Buyers can cancel pending orders without any on-chain refund tx — the USDC was never moved.
- **No SDK upgrade blocked.** Phase 2 ships today with SDK v0.1; on-chain Safe migration is a clean Phase 2b without app-side rewrite (only escrow.ts internal change).
- **AT firehose carries state.** Auditors / arbiter actors / downstream consumers see `escrowOpened` → `escrowRefunded` or `escrowOpened` → `paymentSent` pairs in firehose.
- **Tightened lexicons.** F-Plan bootstrap stubs replaced with proper types + enums + at-uri formats — Phase 2 sub-PRs for the other 44 tsukuru commands get the lexicon discipline started.

## 負の効果 / コスト

- **No actual escrow protection until SDK v0.2.** A malicious manufacturer can't be force-refunded by an arbiter today — buyer's recourse before delivery is only "cancel and trust the record". Mitigation: only do business with manufacturers carrying reputable etzhayyim DID + community trust signals.
- **`safeAddress = 0x0...0` is misleading.** Naive readers might think there's an actual Safe at that address. Mitigation: README documents the placeholder explicitly, and the `escrowOpened.json` lexicon description in this PR is reworded to be clearer.
- **Buyer commitment is record-level only.** A buyer can ignore the intent and never call `pay()` at delivery. Mitigation: manufacturer-side delivery handler will require pay() before marking delivered (Phase 2 next PR).
- **`escrowRefunded` lexicon doesn't exist yet.** The refund writes to `com.etzhayyim.apps.payment.escrowRefunded` but there's no Lexicon JSON for it yet. Filed as inline TODO in `escrow.ts`; PDS validator will throw `Lexicon not found` until the JSON is added. Sub-PR adds the lexicon before any real deploy.

# Alternatives Considered

## A. Wait for SDK v0.2 escrowOpen before shipping tsukuru Phase 2

Pause tsukuru Phase 2 until SDK lands real Safe deployment.

却下理由: SDK v0.2 timeline is unbounded. tsukuru migration timeline is 6-12 months (ADR-2605202800 Phase 1-6); the lexicon + record-pattern work can ship now and is forward-compatible — only `escrow.ts` internals change when SDK v0.2 arrives.

## B. Direct pay() at order create (no escrow)

Skip the intent record. Buyer pays USDC at order creation. Manufacturer holds funds. Cancellation requires manufacturer cooperation.

却下理由: matches the "bad-actor-manufacturer disappears with funds" failure mode from Stripe credit-card disputes. Stripe handles via charge-back; we can't replicate that on-chain without escrow. Unacceptable for B2B production orders that may run $100k+.

## C. Off-chain pre-authorization (e.g., signed permit)

Use ERC-2612 permit() pre-authorization. Buyer signs a permit at order time, manufacturer pulls USDC at delivery.

却下理由: permit() requires USDC support which Coinbase Bridged USDC doesn't have on Base. Native Circle USDC was added 2024 but ERC-2612 permit on it requires verification we haven't done. Filed as v0.2b alternative.

# References

- [ADR-2605202800](./2605202800-tsukuru-etzhayyim-business-model-change.md) — tsukuru full-move Phase 1-6 plan (parent)
- [ADR-2605172000](./2605172000-etzhayyim-kotoba-substrate.md) — kotoba substrate
- [ADR-2605172100](./2605172100-etzhayyim-payments-on-chain-only.md) — payments on-chain only
- [@etzhayyim/sdk pay.ts](../../20-actors/etzhayyim-sdk/src/pay.ts) — SDK v0.1 working path + v0.2 stubs
- [tsukuru kotoba](../../60-apps/etzhayyim-project-tsukuru/kotoba/) — reference impl this ADR documents
- [`payment.escrowOpened.json`](../../00-contracts/lexicons/com/etzhayyim/apps/payment/escrowOpened.json) — Phase 3 wave 4 lexicon (used as intent record schema)
