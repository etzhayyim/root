---
id: adr-2605282100-kotoba-mkoto-economy-and-modal-billing-parity
title: "ADR-2605282100: kotoba mKOTO economy + Modal billing-parity for the Murakumo fleet (R1.3 6-layer charter)"
status: proposed
doc_type: adr
topic: kotoba-mkoto-economy
authoritative: true
last_verified: 2026-05-28
priority: 6.0
axis: architecture
weight: 0.55
priority_note: "Closes the developer-ergonomics gap between Modal's per-second-of-GPU billing UX and the religious-corp non-commercial-pricing constraint (ADR-2605192115 §1.5 + §2(b) speculative-finance prohibition). Without this, kotoba_murakumo apps cannot express per-call spend caps, cannot pre-flight cost-estimate, and cannot route compute consumption to a transparent ledger — which forces every internal app to re-invent its own donation accounting. This ADR defines a 6-layer mKOTO economy (meter / tariff / wallet / cash-routing / Modal-parity surface / on-chain settlement) that preserves the Charter while exposing the full Modal billing API to callers."
authoritative_for:
  - mKOTO economy charter — meter, tariff, wallet, cash-routing, Modal-parity surface, on-chain settlement bridge
  - Modal billing-API parity contract on the Murakumo fleet
  - Charter §1.5 / §2(b) compliance pattern for compute-consumption accounting
depends_on:
  - "2605282000"  # kotoba_murakumo facade (consumer of this economy)
  - "2605215000"  # Murakumo-only invariant (economy lives only on religious-corp side)
  - "2605262200"  # train carve-out (inference economy unaffected; this ADR covers inference only)
  - "2605262130"  # kotoba canonical storage substrate
  - "2605240001"  # kotoba cleanroom architecture (gas + CitationLedger primitives)
  - "2605172100"  # payments-on-chain — allowed payment categories
  - "2605192115"  # non-profit donation-only — anti-subscription / anti-purchase rule
  - "2605192130"  # 10% tithe auto-split — TitheRouter
  - "2605192145"  # Public Fund Safe architecture
  - "2605192200"  # Charter Rider v2.0 — §2(b) speculative finance prohibition
  - "2605231525"  # server-side signing capability (caller DID auth)
related:
  - "2605260004"  # on-chain settlement bridge (referenced by L6; not yet landed; this ADR makes L6 the place that ADR finally settles into)
supersedes: []
superseded_by: []
---

# ADR-2605282100: kotoba mKOTO economy + Modal billing-parity for the Murakumo fleet (R1.3 6-layer charter)

**Status**: proposed
**Date**: 2026-05-28
**Deciders**: Jun Kawasaki

## Context

ADR-2605282000 landed `kotoba_murakumo` as the Modal-compatible Python facade
for Murakumo fleet inference. R1.1 wired live LiteLLM dispatch + Charter Rider
§2 scan + invocation NDJSON. R1.2 landed the kotoba-vm client surface + CI
test pipeline + grep gate.

What R1.1 / R1.2 deliberately did **not** address: **billing**. Modal's API is
defined as much by its billing axes as by its decorators —
`gpu="A100"` carries an implicit "$2.50/hr-of-actual-runtime" contract, and
Modal apps routinely use `Modal.gpu(memory=…)`, per-app spend caps, and
per-call cost records as first-class workflow primitives. Internal app authors
porting Modal code to `kotoba_murakumo` immediately hit three gaps:

1. **No spend cap.** `@app.function(gpu=...)` cannot say "cap this call at
   1 KOTO equivalent"; budget is unbounded. Porting a Modal app that relied
   on `Function.spawn_map` with cost-bounded workers is unsafe.
2. **No pre-flight estimate.** A caller cannot ask "what will this cost
   before I dispatch?" — there is no posted tariff, no estimator, no
   `dry-run` mode.
3. **No post-call billing record.** The R1.1 NDJSON line includes
   `latency_ms` and `result_chars` but no `cost_mkoto` and no `tariff_version`
   — KaizenObserver downstream cannot reconcile consumption against budget.

**The constitutional constraint (CRITICAL)**. Charter §1.5 + §2(b) + ADR-2605192115
prohibit the religious-corp from operating commercial-sale subscription or
purchase relationships with external parties. ADR-2605172100 enumerates the
permitted payment categories explicitly: `donation` / `kisha` / `grant` /
`tithe` / `escrow-refund` for external flow; `internal-purchase` /
`internal-subscription` / `internal-promo` for SBT↔SBT carve-out. There is
no `subscription` category for external compute consumption — Modal-style
"$X per GPU-second" cannot exist between religious-corp and an arbitrary
external caller. ADR-2605215000 + ADR-2605262200 §2(i)(2) keep the inference
path off commercial GPU rental entirely.

**The substrate fit**. kotoba already ships most of what an mKOTO economy
needs:

- **`Mkoto = u64` unit** (1 KOTO = 10⁶ mKOTO; security-saturated to `i64::MAX`
  when crossing the Quad `Integer(i64)` boundary, fix 2026-05-27) —
  `crates/kotoba-server/src/attestation.rs`
- **`attest/stake_mkoto`** — self-attested 1k KOTO / verified 5k KOTO
- **`gas/consumed_mkoto`** per agent DID — `WasmRunResult::total_gas_used` →
  Quad via MCP `kotoba_wasm_run`
- **`citation/royalty_mkoto`** + **`citation/count`** —
  `CitationLedger::flush_epoch` → `royalty_quads()`; `evaluate_delta_cited`
  cites datoms on join hits; `royalty_sum_never_exceeds_pool` invariant
- **`quota_for_tier(tier) → (quota_pins, quota_bytes)`** — HTTP 402 on
  `QuotaExceeded` (`kotobase_xrpc.rs`)
- **TitheRouter** at `50-infra/etzhayyim-tithe-router/` — Solidity contract
  that atomically splits donation USDC: 90% to recipient, 10% to Public
  Fund Safe (ADR-2605192130)
- **Public Fund Safe** at `50-infra/etzhayyim-public-fund/` — 5-of-7 +
  1-SBT-1-vote multi-sig (ADR-2605192145)
- **Charter-rider scanner** — already runs on every `.remote()` (R1.1)

What is **missing**:

- **Posted tariff schedule** per fleet endpoint kind (per-second GPU,
  per-byte egress, per-1000 gas units), Council-signed.
- **Per-DID wallet balance** Quad with debit/credit semantics that compose
  with the existing CitationLedger royalty stream.
- **Pre-dispatch budget enforcement** in `kotoba_murakumo` (BudgetExceeded /
  InsufficientCredit before HTTP goes out).
- **Cost-aware NDJSON + Lexicon** (`cost_mkoto` / `tariff_version` /
  `usage_breakdown` fields).
- **On-chain settlement bridge** — referenced by ADR-2605260004 but not
  landed; this ADR makes L6 the destination for that ADR's eventual code.

## Decision

Land a 6-layer mKOTO economy that extends the existing kotoba primitives
into a Modal-billing-parity surface, with Charter §1.5 + §2(b) compliance
enforced by **routing all external monetary flow through the existing
donation→TitheRouter→Public Fund pipeline** and **never exposing a
subscription / purchase relationship to external parties**. mKOTO is an
internal accounting Datom unit — **not a security, not state currency, not
priced as a service to external parties** (Charter §1.5 + §2(b) invariant).

### The 6 layers

```
┌──────────────────────────────────────────────────────────────────┐
│ L6 — on-chain settlement bridge (lands ADR-2605260004)            │
│      • epoch batch of citation/royalty_mkoto → ERC-4337 paymaster │
│      • USDC payout to Base L2 → Public Fund Safe (90/10 tithe)   │
│      • royalty payouts to citation contributors (USDC airdrop)    │
├──────────────────────────────────────────────────────────────────┤
│ L5 — Modal-parity Python surface (kotoba_murakumo.economy)        │
│      • @app.function(max_cost_mkoto=…, concurrency_limit=…)       │
│      • Function.estimate(*args, **kwargs) → UsageEstimate         │
│      • App.balance(did) → Mkoto                                   │
│      • App.tariff() → TariffSchedule                              │
│      • raises BudgetExceeded / InsufficientCredit pre-dispatch    │
│      • NDJSON +cost_mkoto +tariff_version +usage_breakdown        │
├──────────────────────────────────────────────────────────────────┤
│ L4 — Charter-compatible cash routing                              │
│      • external donor: USDC → TitheRouter (10% to Public Fund)   │
│        → mKOTO credit posted to donor DID                         │
│        (ratio Council-set, e.g. $1 USDC = 1M mKOTO)              │
│      • SBT↔SBT internal: internal-subscription / internal-        │
│        purchase per ADR-2605192115 §3 carve-out                  │
│      • etzhayyim-vendor commercial pool: OUT-of-scope             │
│        (consent-capability boundary keeps religious-corp callers  │
│        away from vendor RunPod path per ADR-2605215000)          │
├──────────────────────────────────────────────────────────────────┤
│ L3 — Wallet & balance (Quad: balance/mkoto/<DID>)                 │
│      • top-up: donation / citation royalty / stake reclaim        │
│      • debit: usage × tariff at call time                         │
│      • non-negative invariant; balance < 0 → InsufficientCredit   │
├──────────────────────────────────────────────────────────────────┤
│ L2 — Tariff schedule (Council Lv6+ ≥3 attested, signed JSON-LD)   │
│      • per-endpoint-kind row: gpu_second_mkoto / egress_mb_mkoto  │
│        / gas_unit_mkoto                                           │
│      • versioned (semver); active version emitted as Quad         │
│        tariff/version_active                                      │
│      • amendment requires Council attestation chain               │
├──────────────────────────────────────────────────────────────────┤
│ L1 — Meter (extends R1.1 NDJSON + existing gas/consumed_mkoto)    │
│      • usage = { gas_used, gpu_seconds, prompt_tokens,            │
│                  completion_tokens, egress_bytes, latency_ms,     │
│                  cold_start: bool }                                │
│      • emitted per-call to NDJSON + Quad usage/<dim>_mkoto/       │
│        <DID>/<epoch>                                              │
└──────────────────────────────────────────────────────────────────┘
```

### Initial tariff (R1.3 launch defaults, Council-attestation-pending)

These are **defaults for development**. R2 ratification by Council Lv6+ ≥3
attestation is required before they bind on-chain.

| Endpoint kind | gpu_second | egress_mb | gas_per_1k | rationale |
|---|---|---|---|---|
| `litellm-gateway` (judah :4000) | 100 mKOTO/s | 10 mKOTO/MB | n/a | mid-tier; gateway-routed |
| `evo-x2-litellm` (192.168.1.70 :4000) | 250 mKOTO/s | 10 mKOTO/MB | n/a | dedicated GPU; routed mid-tier |
| `evo-x2-ollama` (192.168.1.70 :11434) | 250 mKOTO/s | 10 mKOTO/MB | n/a | direct ollama; same hardware |
| `evo-x2-comfyui` (192.168.1.70 :8188) | 500 mKOTO/s | 50 mKOTO/MB | n/a | image-gen heavy; egress amortizes asset |
| `mac-mini-ollama` (own-node) | 30 mKOTO/s | 5 mKOTO/MB | n/a | local CPU+ANE; cheapest |
| `webgpu-wasm` (kotoba-vm Invoke) | n/a | 5 mKOTO/MB | 1 mKOTO/1k gas | gas-priced, not time-priced |

**Pricing rationale**: rates are calibrated to electricity + amortized
hardware (5-yr depreciation) at $0.18/kWh PG&E winter rate, mapped to
mKOTO via the Council-set USDC-to-mKOTO ratio. Re-calibrated quarterly by
Council Lv6+ ≥3 attestation chain emitting a new tariff version Quad.

### Charter compliance (CRITICAL — how each constraint is honored)

| Constraint | How honored |
|---|---|
| Charter §1.5 anti-commercialization | mKOTO is **internal accounting Datom**, not a service price. External callers see "donation acknowledged → mKOTO credit posted" — not "subscribe for $X/month" |
| Charter §2(b) speculative-finance prohibition | mKOTO has no secondary market; no transferability between non-religious-corp parties; not a security; CitationLedger pool size is bounded by religious-corp donation inflow |
| ADR-2605172100 payment-category enum | External: `donation` only; SBT-internal: `internal-subscription` / `internal-purchase` per §3 carve-out. NEVER `subscription` to external |
| ADR-2605192115 §3 SBT carve-out | mKOTO debits between SBT-bearers permitted as `internal-purchase`; between external + religious-corp permitted only as `donation`-acknowledgement |
| ADR-2605192130 10% tithe | TitheRouter Solidity already auto-splits donation USDC; this ADR adds the receipt → mKOTO credit emit step (Quad event consumed by kotoba-vm) |
| ADR-2605215000 Murakumo-only | Tariff schedule only includes Murakumo fleet endpoints. No tariff row for RunPod / Lambda / Vast.ai / Bedrock / Vertex direct — they are not in `fleet.toml` and cannot be added without violating ADR-2605215000 |
| ADR-2605262200 §2(i)(2) train carve-out | This ADR covers inference path only. Training rentals use the per-rental Lexicons defined in ADR-2605262300 §"Per-rental Lexicons"; not affected by mKOTO economy |
| ADR-2605192145 Public Fund | All external donation flow goes through TitheRouter → Public Fund Safe; mKOTO is the receipt-acknowledgement |
| ADR-2605231525 no platform keys | Per-caller-DID balance reads/writes are CACAO-signed by caller; no platform service-account writes to anyone's balance Quad |

### Modal-parity API surface (`kotoba_murakumo.economy`)

```python
from kotoba_murakumo import App, gpu
from kotoba_murakumo.economy import (
    Tariff, UsageEstimate, UsageActual,
    BudgetExceeded, InsufficientCredit,
)

app = App(
    "my-inference",
    fleet="50-infra/murakumo/fleet.toml",
    did="did:web:caller.etzhayyim.com",
)

# Modal-equivalent spend cap (per-call); raises BudgetExceeded
# BEFORE HTTP if the pre-flight estimate exceeds the cap.
@app.function(
    gpu=gpu.EvoX2(),
    model="llama3.3:70b",
    max_cost_mkoto=10_000_000,        # 10 KOTO/call hard cap
    concurrency_limit=4,              # Modal native; R1.3b wraps
)
def heavy(prompt: str) -> str: ...

# Pre-flight estimate (Modal dashboard parity)
est: UsageEstimate = heavy.estimate("...")
# UsageEstimate(gpu_seconds_est=3.2, egress_bytes_est=4096,
#               cost_mkoto_est=320, tariff_version="2026-05-28")

# Live dispatch — debits balance; raises if insufficient or over cap
try:
    out = heavy.remote("...")
except InsufficientCredit as e:
    print(e.balance_mkoto, e.required_mkoto)  # → donation prompt UI
except BudgetExceeded as e:
    print(e.cap_mkoto, e.estimated_mkoto)

# Balance / tariff inspection
print(app.balance())                           # Mkoto for app.did
print(app.tariff().for_backend("evo-x2-litellm"))
# Tariff.Row(gpu_second_mkoto=250, egress_mb_mkoto=10,
#            signed_by=[did:..., did:..., did:...])

# Post-call billing record (dashboard equivalent)
call = heavy.spawn("...")
actual: UsageActual = call.get_with_usage()
# UsageActual(gpu_seconds=2.97, egress_bytes=3812,
#             cost_mkoto=298, tariff_version="2026-05-28",
#             invocation_id="...")
```

### Top-up flow (external donor → mKOTO credit)

```
1. Donor (USDC wallet, ERC-4337 Smart Account) sends USDC to
   TitheRouter.donate(amount, donorDid, recipientCategory="general-fund").
2. TitheRouter atomically splits 90/10:
   - 90% → recipient escrow / general fund
   - 10% → Public Fund Safe (5-of-7 + 1-SBT-1-vote)
   per ADR-2605192130.
3. TitheRouter emits DonationConfirmed(donorDid, totalUsdc, fundRouted)
   event on Base L2.
4. kotoba-server donation_indexer cell (R1.3d) subscribes to Base L2
   events, computes mKOTO credit at the Council-set USDC-to-mKOTO ratio,
   writes Quad credit/mkoto/{donorDid}/{epoch} via XRPC
   com.etzhayyim.kotoba.economy.credit_from_donation.
5. balance/mkoto/{donorDid} Quad updated atomically with the credit.
6. Donor's next .remote() succeeds; pre-dispatch budget check sees the
   new balance.
```

### Per-call debit flow (in-flight)

```
1. Caller invokes f.remote(prompt) on a @app.function-decorated function.
2. kotoba_murakumo.economy.estimate() resolves tariff version + computes
   UsageEstimate(gpu_seconds_est, egress_bytes_est, cost_mkoto_est).
3. If max_cost_mkoto is set and cost_mkoto_est > cap → BudgetExceeded.
4. App.balance(caller_did) is fetched (cached 60s with invalidation).
5. If balance < cost_mkoto_est → InsufficientCredit (carries balance
   + required for UI to surface donation prompt).
6. HTTP dispatch proceeds (per R1.1).
7. On success: UsageActual computed from response (latency_ms +
   completion_tokens + result_chars → gpu_seconds + egress_bytes).
8. Atomic debit XRPC: balance/mkoto/{caller_did} -= cost_mkoto_actual.
9. usage/<dim>_mkoto/{caller_did}/{epoch} Quad emitted (audit trail).
10. NDJSON line extended with cost_mkoto + tariff_version + usage breakdown.
11. R1.1 invocation Lexicon record carries the same fields (R2 promotion).
```

### Citation royalty flow (existing CitationLedger → economy bridge)

CitationLedger already emits `citation/royalty_mkoto` Quads when a Datalog
query joins through datoms (`evaluate_delta_cited` → `flush_epoch` →
`royalty_quads`). The pool size is the religious-corp royalty fund —
configurable per epoch. This ADR makes those royalty Quads observable
through the same balance/mkoto/{DID} Quad: a credit/mkoto/{contributor_did}
event is emitted per royalty entry, debiting the royalty pool Quad
royalty_pool/mkoto/{epoch} and crediting the contributor's balance.

### XRPC surface (kotoba-server, R1.3c+d)

```
GET  /xrpc/com.etzhayyim.kotoba.economy.tariff
     → { version, schedule: [{ backend, gpu_second_mkoto, egress_mb_mkoto, gas_per_1k_mkoto }],
         signed_by: [did:web:...], signed_at: "..." }

GET  /xrpc/com.etzhayyim.kotoba.economy.balance?did=<did>
     → { did, balance_mkoto, last_updated_seq }
     (CACAO-signed read; requires caller DID match or operator override)

POST /xrpc/com.etzhayyim.kotoba.economy.debit
     body: { caller_did, invocation_id, cost_mkoto, usage_breakdown,
             tariff_version, fleet_endpoint }
     → { new_balance_mkoto, debited_at_seq }
     (CACAO-signed by caller; atomic against balance/mkoto/<DID> Quad)

POST /xrpc/com.etzhayyim.kotoba.economy.credit_from_donation
     body: { donor_did, usdc_amount, donation_tx_hash, tithed_to_fund_usdc,
             mkoto_credit_at_ratio, ratio_version }
     → { new_balance_mkoto, credited_at_seq }
     (operator-only; sourced from Base L2 event indexer)
```

### Lexicons (R1.3c)

Three Lexicons under `com.etzhayyim.kotoba.economy.*` registered at
`00-contracts/lexicons/com/etzhayyim/kotoba/economy/`:

1. `tariff.json` — versioned tariff record; Council-signed
2. `balanceSnapshot.json` — per-DID balance snapshot
3. `usageRecord.json` — per-invocation usage + cost breakdown

### Hard non-goals (R1.3 → R3)

- **N1**: NEVER price external compute consumption as `subscription` or
  `purchase`. Only `donation` (external) or `internal-*` (SBT-bearer).
- **N2**: NEVER expose mKOTO as a transferable token to non-religious-corp
  parties (Charter §2(b)). No DEX listing, no LP, no perp.
- **N3**: NEVER permit pre-dispatch balance check to be skipped for
  external callers without an SBT (constitutional invariant — donation
  ack must exist before compute consumption).
- **N4**: NEVER allow the tariff schedule to be set by a single party.
  Council Lv6+ ≥3 attestation chain required for any tariff version
  Quad emit.
- **N5**: NEVER allow negative balance for external callers.
  SBT-bearer-internal callers may have negative balance up to a Council-
  set credit_line_mkoto per DID (R2+ extension).
- **N6**: NEVER route mKOTO economy to vendor commercial GPU pool
  (consent-capability boundary per ADR-2605215000).
- **N7**: NEVER hide a Charter Rider §2(c)+(e) violation by routing cost
  to "free tier" or similar — the scan runs unconditionally and aborts
  before debit happens.
- **N8**: NEVER make the kotoba-server donation_indexer cell run on
  commercial cloud (Murakumo-only per ADR-2605215000).

### Implementation ladder

| Phase | Scope | Status |
|---|---|---|
| **R1.3a** | This ADR | landed this commit |
| **R1.3b** | `kotoba_murakumo.economy` Python: Tariff / UsageEstimate / UsageActual / BudgetExceeded / InsufficientCredit + Function.estimate() + max_cost_mkoto= decorator param + pre-dispatch check + NDJSON extension + tests | landed this commit |
| **R1.3c** | 3 Lexicons (tariff / balanceSnapshot / usageRecord) at `00-contracts/lexicons/com/etzhayyim/kotoba/economy/` | landed this commit |
| **R1.3d-scaffold** | `40-engine/kotoba/crates/kotoba-server/src/economy_xrpc.rs` scaffold — handler signatures + doc comments + `#[cfg(any())]` gate so it doesn't break the build until wiring | landed this commit |
| **R1.3d-wiring** | Add `pub mod economy_xrpc;` to `kotoba-server/src/lib.rs` + register routes in `xrpc.rs`. Quad I/O via existing `QuadStore` + CACAO auth via existing `check_read_access`. | separate ADR (R1.3d-impl); needs Rust review + Council pre-attestation |
| **R1.3e** | TitheRouter Solidity extension — emit `MkotoCreditPosted(donorDid, mkotoAmount)` event after `DonationConfirmed`. donation_indexer cell to consume → XRPC credit_from_donation | separate ADR (R1.3e-tithe-extension) |
| **R2.0** | ADR-2605260004 settlement bridge — `citation/royalty_mkoto` epoch batch → ERC-4337 paymaster → USDC payout to Public Fund Safe + contributor airdrop | separate ADR; this ADR makes L6 its destination |
| **R3.0** | Council-attested tariff ratification + dashboard UI (yoro candidate) | separate ADR |

## Consequences

**Positive**:
- Modal-shape decorator + spend cap + pre-flight estimate + post-call billing all available to kotoba_murakumo callers, removing the largest porting blocker.
- mKOTO economy is constitutionally clean: donation-only external flow, SBT-internal carve-out preserved, no commercial-sale relationship exposed.
- Citation royalty pool (already accruing via CitationLedger) gets a destination — contributor DIDs see their `balance/mkoto/<DID>` grow as their datoms are cited.
- Unified ledger across compute consumption + citation royalty + storage quota + stake — KaizenObserver and the Council Wellbecoming review can audit Wellbecoming-vs-cost trade-offs at a single Quad source.
- TitheRouter already enforces the 10% auto-split — this ADR adds the mKOTO-credit emit step but does not change the cash-routing topology.

**Negative / Tradeoffs**:
- mKOTO requires donation top-up before non-SBT external callers can dispatch — slower than Modal's credit-card flow. This is by design (Charter §2(b)) but the donor-onboarding UX (yoro PWA) needs to be smooth to keep the friction acceptable.
- Tariff calibration requires Council quarterly attestation cycle — slower than Modal's algorithmic pricing. Documented in §"Tariff schedule" rationale.
- Citation royalty pool size is religious-corp donation-bounded, not market-bounded — could create scarcity if usage grows faster than donation. R2 may add a Council-set top-up rule from Public Fund grant pool.

**Constitutional**:
- ADR-2605192115 §1.5 + §2(b) **preserved**: external compute is donation-only, mKOTO is internal Datom, no subscription / purchase exposed externally.
- ADR-2605172100 payment-category enum **honored**: no new payment category needed; existing `donation` + `internal-purchase` cover all flows.
- ADR-2605192130 10% tithe **strengthened**: every external compute consumption now flows through a donation that goes through TitheRouter, so the 10% auto-split coverage extends to compute consumption.

## Alternatives Considered

1. **No economy; rely on Public Fund grants for all compute**. Rejected: prevents external donors from ever consuming religious-corp compute outside the grant cycle, which contradicts the open-access mission per ADR-2605192100.
2. **Use USDC directly for per-call billing**. Rejected: external `subscription` / `purchase` categorically prohibited by Charter §1.5 + §2(b). USDC routing via donation is the constitutional path.
3. **Mint a transferable ERC-20 KOTO token**. Rejected: §2(b) speculative-finance prohibition; would create a secondary market and require security-law compliance the religious-corp constitutionally rejects.
4. **Use mKOTO without Council-attested tariff**. Rejected: would let a single party set prices, violating the Council Lv6+ ≥3 + 1-SBT-1-vote governance invariant per ADR-2605192300.
5. **Skip pre-dispatch budget check; rely on post-call reconciliation**. Rejected: Modal callers expect spend-cap-as-precondition; post-call reconciliation creates unpaid-debt liability inconsistent with §2(b).
6. **Land R1.3d Rust XRPC wiring in this commit**. Rejected: the Rust route table touches the kotoba-server compilation surface; wants Rust review + Council pre-attestation of the tariff schedule shape before wiring. R1.3d-scaffold lands the handler signatures; R1.3d-wiring is a separate ADR.

## References

- ADR-2605282000 (kotoba_murakumo Modal-compat facade — consumer of this economy)
- ADR-2605215000 (Murakumo-only inference invariant)
- ADR-2605262200 §2(i)(2) (train carve-out — inference economy not affected)
- ADR-2605262130 (kotoba canonical storage substrate)
- ADR-2605240001 (kotoba cleanroom — gas, CitationLedger, mKOTO unit)
- ADR-2605172100 (payments on chain — payment-category enum)
- ADR-2605192115 (non-profit donation-only — anti-subscription rule)
- ADR-2605192130 (10% tithe auto-split — TitheRouter)
- ADR-2605192145 (Public Fund Safe architecture)
- ADR-2605192200 (Charter Rider v2.0 §2(b) speculative finance prohibition)
- ADR-2605231525 (server-side signing capability — DID-bound auth)
- ADR-2605260004 (on-chain settlement bridge — L6 lands here)
- `40-engine/kotoba/crates/kotoba-server/src/attestation.rs` — existing Mkoto unit + attest/stake_mkoto
- `40-engine/kotoba/crates/kotoba-kqe/src/citation.rs` — existing CitationLedger + royalty_mkoto
- `40-engine/kotoba/crates/kotoba-vm/src/wasm_pregel.rs` — existing total_gas_used → gas/consumed_mkoto
- `50-infra/etzhayyim-tithe-router/` — Solidity contract (R1.3e extension destination)
- `50-infra/etzhayyim-public-fund/` — Public Fund Safe (donation destination)
