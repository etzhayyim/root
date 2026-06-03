---
id: 2605212050-etzhayyim-stripe-erc4337-bridge-split
title: "Stripe Issuing → ERC-4337 Bridge — Vendor (Fiat) and etzhayyim (Chain) Split"
status: active
doc_type: adr
topic: etzhayyim-fiat-bridge
authoritative: true
last_verified: 2026-05-21
priority: 8.0
axis: payments
weight: 0.80
priority_note: "Resolves ADR-2605211950 Open Item 4. Specifies how the existing vendor-side Stripe Issuing → ERC-4337 + USDC bridge splits across the substrate centralization axis: Stripe (centralized primitive) stays vendor; ERC-4337 + USDC settlement (decentralized primitive) moves to etzhayyim. The two sides connect via a vendor → etzhayyim XRPC call backed by an etzhayyim-held USDC treasury reserve."
authoritative_for:
  - bridge architecture for fiat (Stripe Issuing) → on-chain (USDC on Base L2) settlement
  - org.etzhayyim.payment.creditFromFiat XRPC contract (vendor → etzhayyim)
  - USDC reserve treasury structure (etzhayyim-controlled, vendor-backed)
  - tithe routing for fiat-originated chain credits (10% to Public Fund)
  - refund flow + solvency gating + Council-multisig daily cap
related:
  - "ADR-2605211950 (substrate centralization axis)"
  - "ADR-2605172100 (etzhayyim payments on-chain only)"
  - "ADR-2605192130 (10% tithe → Public Fund)"
  - "ADR-2605192115 (donation-only + SBT carve-out)"
  - "ADR-2605212030 (etzhayyim authz ERC725 root issuance)"
  - "ADR-2605212040 (etzhayyim K2 ecosystem)"
depends_on:
  - "ADR-2605211950"
  - "ADR-2605172100"
  - "ADR-2605212030"
supersedes: []
superseded_by: []
---

# ADR-2605212050: Stripe Issuing → ERC-4337 Bridge — Vendor (Fiat) and etzhayyim (Chain) Split

**Status**: active
**Date**: 2026-05-21
**Deciders**: Jun Kawasaki

## Context

Vendor currently runs a "Stripe Issuing → ERC-4337 + USDC" bridge: a Stripe Issuing card swipe triggers a webhook in vendor; vendor mints a matching ERC-4337 UserOp and settles USDC to the recipient on the vendor private chain. The bridge is documented in vendor `60-apps/etzhayyim-project-murakumo/CLAUDE.md` and ADR-2604262100.

Under ADR-2605211950 (substrate centralization axis):

- **Stripe Issuing** is a centralized primitive — stays in vendor.
- **ERC-4337 + USDC settlement** is a decentralization primitive — must move to etzhayyim.
- The vendor private chain `260425` is not used by etzhayyim (per ADR-2605212030 D1); Base L2 is the etzhayyim chain.
- Etzhayyim payments are on-chain only and run through the etzhayyim Tithe Router (10% auto-split to Public Fund per ADR-2605192130).

The bridge must be re-architected so that:

1. Vendor retains the Stripe webhook handler and the fiat receivable accounting.
2. Etzhayyim performs the on-chain mint / transfer of USDC on Base L2.
3. The two sides connect via a typed XRPC call with a clear trust boundary.
4. Tithe routing applies to chain-side flows.
5. Solvency is gated — etzhayyim never mints USDC it does not back.
6. Refunds reverse the flow cleanly.
7. A daily cap, governed by Council multisig, caps exposure.

## Decision

### D1. Architecture — two-stage flow with vendor → etzhayyim XRPC handoff

```
┌─────────────────────────────────────────────────────────────────┐
│                            VENDOR                               │
│                                                                  │
│  1. user card swipe                                             │
│      → Stripe Issuing realtime authorization                     │
│      → vendor webhook (`/stripe/issuing/authorization`)          │
│      → vendor approves authorization (subject to internal        │
│        Stripe rules + per-user limit)                            │
│      → vendor records fiat receivable in RisingWave              │
│        (`vertex_etzhayyim_stripe_issuing_authorization`)              │
│      → vendor calls etzhayyim XRPC (D3 below):                   │
│        `org.etzhayyim.payment.creditFromFiat`                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                                  │
                       x-internal-trust JWT
                       (vendor service identity)
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                          ETZHAYYIM                              │
│                                                                  │
│  2. XRPC handler in `50-infra/etzhayyim-fiat-bridge/`           │
│      → verify vendor JWT                                         │
│      → check daily cap (Council-multisig governed, D6 below)    │
│      → check treasury reserve solvency (D5 below)               │
│      → submit ERC-4337 UserOp via etzhayyim-k2 bundler:         │
│        treasury → recipient.smartWallet, USDC amount            │
│      → tithe 10% to Public Fund (ADR-2605192130) via            │
│        etzhayyim-tithe-router atomic split                       │
│      → write AT Record:                                         │
│        `org.etzhayyim.payment.fiatBridgeReceipt`                │
│        anchored to MST → IPFS → Base L2 (ADR-2605171800)        │
│      → return chain tx hash + receipt to vendor                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The handler lives in a **new** etzhayyim service: `50-infra/etzhayyim-fiat-bridge/`. It is the only etzhayyim-side touchpoint for vendor fiat events.

### D2. Trust boundary — x-internal-trust JWT (vendor service identity)

Vendor → etzhayyim XRPC calls authenticate via an **x-internal-trust** JWT signed by a vendor service key registered in etzhayyim authz (per ADR-2605212030). The JWT carries:

- `iss`: vendor service DID (`did:web:authz.etzhayyim.com` or per-service did:web)
- `aud`: `org.etzhayyim.payment.creditFromFiat`
- `exp`: ≤ 60s TTL
- `nonce`: single-use, tracked in etzhayyim service KV
- claim `vendor_authorization_id`: Stripe Issuing authorization id (for cross-reference)

Etzhayyim treats vendor as a known fiat upstream — but not as a peer governance entity. The JWT proves the *call comes from vendor* but does not constitute Council authorization. Council-multisig governs the cap (D6), not per-call approval.

### D3. XRPC contract — `org.etzhayyim.payment.creditFromFiat`

Procedure NSID (new lexicon under `00-contracts/lexicons/org/etzhayyim/payment/`):

| Field | Direction | Type | Description |
|---|---|---|---|
| `vendorAuthorizationId` | in | string | Stripe Issuing authorization id |
| `amountUSDCMicros` | in | integer | USDC amount in micro-USDC (1 USDC = 10^6) |
| `recipientDid` | in | string | etzhayyim-format did:web or did:erc725:base |
| `recipientSmartWalletAddress` | in | string | 0x-address of recipient's ERC-4337 Smart Wallet on Base L2 |
| `purposeNarrow` | in | string | enum: `donation` / `kisha` / `grant` / `tithe-passthrough` / `escrow-refund` / `internal-purchase` / `internal-subscription` / `internal-promo` (per ADR-2605192115 §4) |
| `idempotencyKey` | in | string | vendor-generated UUID for retry safety |
| `vendorJWT` | in (header `x-internal-trust`) | string | JWT per D2 |
| `chainTxHash` | out | string | Base L2 transaction hash (post-confirmation) |
| `fiatBridgeReceiptAtUri` | out | string | AT URI of the on-chain-anchored receipt record |
| `titheTxHash` | out | string | Base L2 tx hash for the 10% Public Fund split |
| `effectiveAmountUSDCMicros` | out | integer | amount after tithe (`= amountUSDCMicros * 0.9`) |

Errors:

| code | semantics |
|---|---|
| `Unauthorized` | vendor JWT invalid / expired / wrong audience |
| `DailyCapExceeded` | aggregate amount across vendor calls today exceeded Council-multisig cap |
| `InsufficientTreasuryReserve` | etzhayyim USDC treasury balance < `amountUSDCMicros` |
| `RecipientUnverified` | `recipientDid` does not resolve to a valid etzhayyim root or does not match `recipientSmartWalletAddress` |
| `PurposeNarrowRejected` | `purposeNarrow` not in the allowed enum or violates ADR-2605192115 SBT↔SBT carve-out rules |
| `Idempotent` (not an error) | call with seen `idempotencyKey` returns the prior receipt |

### D4. Tithe routing — 10% on chain side via etzhayyim-tithe-router

The 10% Public Fund tithe (ADR-2605192130) applies to the **chain side**, not the fiat side. Vendor accounting books the full fiat receipt; etzhayyim receives 100% USDC into treasury and atomically:

1. Mints 90% × `amountUSDCMicros` to `recipientSmartWalletAddress` via ERC-4337 UserOp.
2. Mints 10% × `amountUSDCMicros` to the Public Fund 5-of-7 Safe via the same atomic UserOp (or a Permit2 split).

The atomic split is enforced by the existing `etzhayyim-tithe-router` contract. The XRPC handler does not bypass the router; it submits one UserOp that the router decomposes into the two transfers.

If `purposeNarrow` is in the SBT↔SBT internal carve-out (`internal-purchase` / `internal-subscription` / `internal-promo` per ADR-2605192115 §3), the tithe is still applied — there is no internal-purchase tithe exemption.

### D5. Treasury reserve — etzhayyim-controlled, vendor-backed

Etzhayyim maintains a **dedicated USDC reserve** on Base L2 at `etzhayyim-fiat-bridge/contracts/Reserve.sol`. The reserve has two roles:

| Role | Holder | Authority |
|---|---|---|
| **Custody** | etzhayyim (5-of-7 Council multisig Safe) | only Council multisig can withdraw |
| **Backing** | vendor (etzhayyim Japan) | vendor's fiat receivables (Stripe outstanding) back the on-chain balance |

Vendor deposits USDC into the reserve as part of regular treasury operations (e.g. monthly net settlement: vendor's gross fiat inflows minus its operating costs → top-up the reserve). The reserve drains as etzhayyim mints USDC for bridge calls.

The XRPC handler in D3 returns `InsufficientTreasuryReserve` if a call would drive the reserve below a configured minimum (default: 30 days of average burn). Vendor then refunds the Stripe authorization and the user sees a declined card.

This makes etzhayyim's solvency invariant: **etzhayyim never mints USDC it does not have**. If vendor's fiat backing fails (Stripe outage, bank failure, vendor insolvency), the reserve may run dry, but no synthetic USDC enters circulation.

### D6. Daily cap — Council-multisig governed

The maximum aggregate `amountUSDCMicros` allowed across all `creditFromFiat` calls per UTC day is a **mutable** constant in `etzhayyim-fiat-bridge/contracts/Reserve.sol`, governed by Council 5-of-7 multisig.

Initial value: **TBD — proposed 50,000 USDC/day** (suitable for early scale; revisit when traffic warrants).

Rationale:

- Caps blast radius if vendor service key is compromised.
- Caps blast radius if vendor accidentally double-fires authorizations.
- Provides a constitutional governance handle (Council can throttle the bridge without breaking on-chain payments).
- Multisig governance avoids per-call Council friction.

Cap changes follow the standard Council mutable-constant procedure (5-of-7 with constitutional review).

### D7. Refund — reverse flow, chain refund triggers Stripe refund

User-initiated refunds flow chain-first:

```
recipient asks for refund
  → recipient calls org.etzhayyim.payment.requestFiatBridgeRefund(receiptAtUri)
  → etzhayyim verifies receipt + recipient signature
  → etzhayyim mints reverse UserOp: recipient → reserve, plus
    Public Fund refunds 10% to reserve (tithe-router reverse split)
  → etzhayyim writes org.etzhayyim.payment.fiatBridgeRefundReceipt AT Record
  → etzhayyim calls back vendor XRPC: com.etzhayyim.authz.fiatBridgeRefundCallback
    (vendor side; vendor reverses the Stripe Issuing authorization or
    issues a Stripe refund depending on settlement state)
```

The chain side is always reversed first; the fiat side follows. This is symmetric to the forward flow (fiat first → chain) and guarantees that the on-chain receipt never references a fiat charge that has been silently reversed.

Vendor MUST honor `fiatBridgeRefundCallback` within 24h or the etzhayyim receipt records a `vendor_refund_pending` flag. Persistent failures escalate to Council.

## Consequences

- New etzhayyim service: `50-infra/etzhayyim-fiat-bridge/`.
  - `contracts/Reserve.sol` (Foundry, Council-multisig owned)
  - `src/` XRPC handler (k8s pod, calls etzhayyim-k2 bundler)
  - `scripts/treasury-top-up.ts` (vendor-callable for reserve replenish)
- New lexicons under `00-contracts/lexicons/org/etzhayyim/payment/`:
  - `creditFromFiat.json` (procedure)
  - `requestFiatBridgeRefund.json` (procedure)
  - `fiatBridgeReceipt.json` (record)
  - `fiatBridgeRefundReceipt.json` (record)
- New vendor-side lexicons (vendor repo, separate PR):
  - `com.etzhayyim.authz.fiatBridgeRefundCallback` (procedure, etzhayyim → vendor)
- Vendor `60-apps/etzhayyim-project-murakumo/CLAUDE.md` and Stripe Issuing description sections updated to reflect the new flow (vendor approves authorization → calls etzhayyim XRPC → records receipt). Vendor private chain `260425` no longer involved in fiat → chain settlement.
- Tithe receipts per ADR-2605192130 increase — every fiat-originated chain credit contributes to the Public Fund. This is the intended design.
- Treasury reserve becomes a single point of operational risk: depletion = bridge unavailable. Mitigation: minimum-balance alarm + vendor SOP for monthly top-up.
- Council gains a daily-cap throttle as a governance lever over the fiat flow.
- The vendor-side reading of vendor's `vertex_etzhayyim_stripe_issuing_authorization` table joins to the etzhayyim chain receipt via `vendorAuthorizationId`. Cross-repo data join lives in vendor analytics; etzhayyim does not import vendor RisingWave.

## Alternatives Considered

1. **Keep the bridge entirely in vendor (status quo).** Rejected: violates ADR-2605211950 substrate axis — on-chain mint of USDC is a decentralization primitive that cannot live in vendor.

2. **Have vendor mint USDC directly on Base L2 using a vendor-held key.** Rejected: equivalent to (1). Vendor holding chain mint authority puts decentralization primitive operation in a centralized entity. Treasury must be Council-controlled.

3. **Synchronous fiat → chain (single transaction).** Rejected: Stripe Issuing realtime authorization is fast (~100 ms); Base L2 confirmation is ~2 s. Coupling them in a single transaction means Stripe declines on chain latency. The chosen design treats fiat approval as the realtime contract; chain settlement is async batched (return chain tx hash to vendor after confirmation).

4. **Skip the Public Fund tithe on fiat-originated credits.** Rejected: ADR-2605192130 applies the 10% tithe to all donation / kisha / grant inflows; the fiat origin does not exempt them. Doing so would create an accounting incentive to route everything via fiat to avoid the tithe.

5. **Use a separate stablecoin (DAI / FRAX) for the bridge.** Rejected: ADR-2605172100 already commits to USDC on Base L2 (`0x833589...`). Adding a second stablecoin doubles ops without solving anything.

6. **No daily cap — trust the JWT.** Rejected: a compromised vendor service key could drain the reserve. Daily cap is a defense-in-depth against operational compromise. Cap value is governance-tunable.

7. **Vendor holds the reserve.** Rejected: vendor holding the USDC reserve means the chain side is gated on vendor solvency directly, and Council has no authority over the bridge. Council-multisig custody is the constitutional alignment.

## Open Items

- Decide the initial daily cap value (proposed 50,000 USDC; awaiting Council confirmation).
- Decide the reserve minimum-balance threshold (proposed 30 days of average burn; needs traffic data).
- Define vendor SOP for monthly treasury top-up (which bank wire path → Coinbase / Circle Mint → Base L2 USDC → reserve).
- Lexicon NSIDs: confirm `org.etzhayyim.payment.creditFromFiat` (this ADR) vs alternative under existing `com.etzhayyim.apps.payment.*` namespace. Recommended: `org.etzhayyim.payment.*` for new endpoints to mirror ADR-2605212030 namespace decision.
- Reserve contract implementation choice — bare Solidity vs OpenZeppelin Governor vs Safe-only. Recommended: Safe (5-of-7) with a thin module exposing the cap-check + mint-helper for the XRPC handler.
- Vendor authorization id ↔ etzhayyim receipt cross-reference SLA — how long does vendor retain `vertex_etzhayyim_stripe_issuing_authorization` rows? Match etzhayyim AT Record retention.
- Failure mode: what if the etzhayyim bundler is down at the moment of vendor → etzhayyim call? Buffer with retry queue vs return error to Stripe (decline). Recommended: short retry (≤ 2s) then decline; never queue across the Stripe authorization window.

## References

- ADR-2605211950 — substrate centralization axis
- ADR-2605172100 — etzhayyim payments on-chain only
- ADR-2605192130 — 10% Tithe → Public Fund
- ADR-2605192115 — donation-only + SBT↔SBT carve-out
- ADR-2605212030 — etzhayyim authz ERC725 root issuance (vendor JWT signing)
- ADR-2605212040 — etzhayyim K2 ecosystem (bundler dependency)
- ADR-2605171800 — langgraph MST IPFS L2 anchor pipeline
- `50-infra/etzhayyim-paymaster/` — shared ERC-4337 paymaster
- `50-infra/etzhayyim-tithe-router/` — atomic 10% split
- `50-infra/etzhayyim-public-fund/` — 5-of-7 Safe destination
- Vendor: `60-apps/etzhayyim-project-murakumo/CLAUDE.md` (current Stripe Issuing → ERC-4337 description — migration source)
- Vendor: ADR-2604262100 (k8s + ERC-4337 + IPFS — migration source)
