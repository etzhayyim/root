# tsukuru rw-free

Phase 2 reference implementation of tsukuru on the etzhayyim substrate.

Per [ADR-2605202800](../../../90-docs/adr/2605202800-tsukuru-etzhayyim-business-model-change.md), tsukuru migrates from vendor's `createKyselyDb` + Stripe Issuing pattern to the etzhayyim RW-free + on-chain-only substrate ([ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) + [ADR-2605172100](../../../90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md)).

This package implements **9 of 46** tsukuru XRPC commands as reference:

- `productionOrder.createProductionOrder` (slice 1)
- `productionOrder.cancelProductionOrder` (slice 1)
- `qualityInspection.submitInspection` (slice 2)
- `qualityInspection.getInspections` (slice 2)
- `manufacturerRegistry.registerManufacturer` (slice 3)
- `manufacturerRegistry.getManufacturer` (slice 3)
- `manufacturerRegistry.listManufacturers` (slice 3)
- `manufacturerRegistry.searchManufacturers` (slice 3)
- `manufacturerRegistry.getManufacturerStats` (slice 3)

The remaining 37 commands (`factoryRegistry.*`, `productionProgress.*`, `productionOrder.{get,list,updateStatus,estimateLeadTime}`, `manufacturingCell.*`, `manufacturingOutput.*`, `softwareIntegration.*`, `logisticsRoute.*`, `autonomyOperation.*`, `supplierExchange.*`, `euv.*`, `cnt.*`) follow the same pattern and are deferred to follow-up Phase 2 sub-PRs.

## Pattern translation

| Vendor (`tsukuru.gftd.ai`) | etzhayyim (`tsukuru.etzhayyim.com`) |
|---|---|
| `createKyselyDb().insertInto("vertex_tsukuru_*").values({...})` | `e.write({ collection, record })` |
| `recordWrite(sdk, "ai.gftd.apps.tsukuru.*", {...})` | `e.write({ collection, record })` |
| `invoke(sdk, "did:web:stripe.gftd.ai", "chargeCustomer", {...})` | `escrow.openIntent(e, {...})` (no on-chain tx) |
| `invoke(sdk, "did:web:stripe.gftd.ai", "cancelCard", {...})` | `escrow.refundIntent(e, {...})` (no on-chain tx) |
| `payment.method === "stripe_issuing"` + `stripeCardId` | `payment.method === "escrow_intent"` + escrow record URI |

## Escrow flow (deferred-payment intent — full loop)

```
   create order (escrow_intent)
     │
     └─► openIntent()
           writes ai.gftd.apps.payment.escrowOpened
           safeAddress / arbiter = 0x0...0 placeholder (SDK v0.1)
           NO on-chain USDC transfer
           returns escrowIntentUri
           │
           └─► createProductionOrder() binds escrowIntentUri to record

   delivery confirmed (slice 2 — qualityInspection)
     │
     └─► submitInspection(result="pass")
           writes ai.gftd.apps.tsukuru.qualityInspection
           │
           └─► settleEscrow()  →  SDK pay()
                 USDC.transfer to manufacturer wallet on Base L2
                 writes ai.gftd.apps.payment.sent (auto by SDK)
                 returns paymentSentUri + txHash
                 │
                 └─► markOrderPassed()
                       productionOrder.status = "delivered"
                       productionOrder.paymentSentUri = ...
                       inspection.paymentSentUri = ...

   cancel before delivery (slice 1)
     │
     └─► refundIntent()
           writes ai.gftd.apps.payment.escrowRefunded
           NO on-chain tx (USDC was never moved)
           returns escrowRefundUri
           │
           └─► cancelProductionOrder() writes updated productionOrder
                with status=cancelled + escrowRefundUri
```

This is **record-state-machine escrow**, not on-chain escrow. State transitions are enforced by application logic + AT firehose audit trail, not by a Safe 2-of-3 contract. Migration to on-chain Safe-based escrow happens when [`@etzhayyim/sdk`](../../../20-actors/etzhayyim-sdk/src/pay.ts) ships v0.2 `escrowOpen()` / `escrowRelease()` (currently throws `"v0.2+"`).

## Usage

```ts
import { Etzhayyim } from "@etzhayyim/sdk";
import {
  createProductionOrder,
  cancelProductionOrder,
  submitInspection,
  getInspections,
} from "@etzhayyim/tsukuru-rw-free";

const e = new Etzhayyim({
  did: "did:web:customer.etzhayyim.com",
  pdsUrl: "https://pds.etzhayyim.com",
  l2RpcUrl: "https://mainnet.base.org",
  // ... session or auth
});

// 1. Create
const out = await createProductionOrder(
  e,
  {
    manufacturerDid: "did:web:tsukuru.etzhayyim.com:manufacturer:acme-precision",
    customerDid: "did:web:customer.etzhayyim.com",
    productSpec: { sku: "WIDGET-A", quantity: 100, cadCid: "bafy..." },
    fulfillmentMode: "bto",
    priority: "normal",
    payment: {
      method: "escrow_intent",
      amountUsdcMicros: 10_000_000_000, // 10,000 USDC
    },
  },
  { manufacturerWalletAddress: "0xACME...DEAD" }
);
// → { productionOrderUri, status: "pending", escrowIntentUri, ... }

// 2a. Cancel before delivery (record-only refund)
const cancel = await cancelProductionOrder(e, {
  productionOrderUri: out.productionOrderUri,
  reason: "spec change requested by buyer",
  cancelledByDid: "did:web:customer.etzhayyim.com",
});
// → { status: "cancelled", escrowRefundUri }

// 2b. OR — submit passing inspection at delivery (triggers settlement)
const inspect = await submitInspection(
  e,
  {
    productionOrderUri: out.productionOrderUri,
    inspectorDid: "did:web:qa-agent.etzhayyim.com",
    inspectionType: "final",
    result: "pass",
    defectRatePpm: 50,
    findings: ["all units within spec"],
    lotNumber: "L20260520-A",
  },
  {
    manufacturerWallet: "0xACME...DEAD",
    buyerPrivateKey: "0x..." as `0x${string}`, // Phase 2b+ replaces with smart-wallet signer
  }
);
// → { status: "settled", inspectionUri, paymentSentUri, txHash, ... }

// 3. List inspections
const list = await getInspections(e, {
  productionOrderUri: out.productionOrderUri,
});
// → { items: [InspectionView], total }
```

## What this package IS / ISN'T

**IS**:
- Reference implementation of 2 tsukuru commands on the etzhayyim substrate.
- Documentation (via code) of the vendor-Stripe → etzhayyim-escrow pattern translation.
- Type definitions aligned with the tightened lexicons (`productionOrder.{create,cancel}ProductionOrder.json` updated in this same PR).
- Module that builds standalone with @etzhayyim/sdk — `pnpm typecheck` passes.

**ISN'T**:
- A deployed Worker — there's no XRPC handler glue yet. Wiring lands when the etzhayyim Worker framework matures (see open-isco/rw-free for the seed.ts / query.ts CLI pattern as the current usage model).
- A production replacement for `tsukuru.gftd.ai` — vendor production runs with Stripe + RW until Phase 5 cutover (per ADR-2605202800 timeline 6-9 months).
- The full 46-command parity — 44 commands remain to be ported (Phase 2 follow-ups).
- On-chain escrow — Phase 2 is record-only intent; migration to Safe 2-of-3 lands when SDK v0.2 ships `escrowOpen()` / `escrowRelease()`.

## Related

- [ADR-2605202800](../../../90-docs/adr/2605202800-tsukuru-etzhayyim-business-model-change.md) — tsukuru full-move Phase 1-6 plan
- [ADR-2605202900](../../../90-docs/adr/2605202900-tsukuru-phase2-escrow-intent-pattern.md) — Phase 2 escrow_intent pattern design (this PR)
- [ADR-2605172000](../../../90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) — RW-free substrate
- [ADR-2605172100](../../../90-docs/adr/2605172100-etzhayyim-payments-on-chain-only.md) — payments on-chain only
- [@etzhayyim/sdk](../../../20-actors/etzhayyim-sdk/) — SDK reference
- [open-isco rw-free](../../ai-gftd-project-open-isco/rw-free/) — sibling reference impl (seeder + query CLI pattern)
