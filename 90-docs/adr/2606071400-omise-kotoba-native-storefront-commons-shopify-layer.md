---
id: adr-2606071400-omise-kotoba-native-storefront-commons
title: "ADR-2606071400: omise お店 — kotoba-native storefront commons (Shopify-layer for internal sellers); promote scaffold → implementation"
status: proposed
doc_type: adr
topic: omise-storefront-commons
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/omise
depends_on:
  - 2606012100   # okaimono provisioning commons (buyer-side sibling; omise feeds Ring 1)
  - 2605302000   # warifu zero-fee settlement
  - 2605262130   # kotoba storage substrate
  - 2605181100   # encrypted envelope
related:
  - 2605231525   # no-server-key
supersedes: []
superseded_by: []
---

# ADR-2606071400: omise お店 — kotoba-native storefront commons (Shopify-layer for internal sellers); promote scaffold → implementation

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

`omise` exists today only as a **legacy JSON-LD scaffold** (`actor-manifest.jsonld` +
`CLAUDE.md`, ~179 lines, zero executable cells), authored before the kotoba-substrate
unification (ADR-2605262130) and the `okaimono` charter-clean commerce pattern
(ADR-2606012100). Two problems:

1. **Architecture drift.** Its manifest describes a Platform/Seller/Buyer marketplace persisted
   the *old* way (collections + implied RisingWave/SQL read path), which the substrate boundary
   now forbids (kotoba EAVT only; no RisingWave/SQL/Lance as canonical).
2. **Charter ambiguity + overlap with okaimono.** As written it is a generic Shopify clone
   (multi-tenant merchant platform with checkout SAGA), with no inversion stance, and it
   overlaps `okaimono`'s buyer-side commerce commons.

We resolve both by **promoting `omise` to a kotoba-native implementation with a sharp,
non-overlapping niche.**

**Niche (the clean split from okaimono):**
- `okaimono` = **buyer-side** demand commons (discover → compare → basket → assisted checkout).
- `omise` = **seller-side** storefront enablement — the **Shopify layer**: it lets an
  etzhayyim **producing-actor** (yakushi, makura, mitsuho, sanae, …) or a **member** stand up a
  storefront (catalog, inventory, order, fulfilment handoff) whose listings **feed
  `okaimono` Ring 1**. omise is merchant *tooling for the commons*, not a third-party
  marketplace.

# Decision

Rewrite `omise` as a **kotoba-EAVT-native Tier-B actor**, mirroring the `okaimono` structure
(manifest.edn + lex/*.edn + cells/*.edn + kotoba/schema.edn + py cells + tests). R0 = data model
+ cell scaffolds + tests; landing path follows okaimono's R-cadence.

**Charter-clean inversions (gates, see manifest.edn):**

| Shopify term | omise charter-clean dual | gate |
|---|---|---|
| platform takes %/txn + subscription tiers | **zero commission, zero subscription**; sellers are internal actors/members; settlement USDC + TitheRouter 10 % via warifu | G2 no-commission |
| open third-party merchant onboarding | **SBT-gated sellers** (producing-actor or member); Phase-2 external seller = Council Lv7+ | G3 seller-gating |
| Shopify Payments / Stripe | warifu rails; member/actor signs; **no server-held key** | G7 / G15 no-server-key |
| ad surfaces, "boost", paid placement | **data-only catalog, no sponsored ranking**; commons-first ordering | G4 no-ads |
| engagement/conversion dark-patterns | Wellbecoming ordering (durability/repairability/labor-provenance surfaced), no urgency/scarcity | G5 anti-dark |
| RisingWave/SQL storefront DB | **kotoba Datoms** (storefront/listing/order/fulfilment) | G6 kotoba-eavt-native |

**Composition:** omise `listing` Datoms are exactly the shape `okaimono`'s `catalog` cell reads
as Ring-1 `:product/ring "internal"` — so an omise storefront is *automatically* discoverable in
okaimono with no integration glue. Fulfilment hands off to `todoke`/logistics actors (G8
labor-dignity). Order → settlement → TitheRouter is the warifu flow.

**Scope at R0:** kotoba-native `manifest.edn`, lex (`storefront`, `listing`, `order`,
`fulfilment`, `settlement`), cell scaffolds (`storefront` datalog, `list` langgraph, `order`
langgraph, `settle` datalog), kotoba schema + `:representative` seed, py agent + tests mirroring
okaimono. The legacy `actor-manifest.jsonld` is retained one R-cycle with a deprecation banner,
then removed (no RisingWave path ships).

# Consequences

- omise stops being a charter-ambiguous Shopify clone and becomes the **seller-side commons**
  that feeds okaimono — the two compose into a full charter-clean commerce surface (supply +
  demand) without duplication.
- Removes a substrate-boundary violation (legacy SQL-shaped manifest) from the roster.
- Implementation is *templated* on okaimono (proven, 40/40 tests), lowering risk: net-new work
  is the seller/storefront/order semantics, not new substrate plumbing.

# Alternatives Considered

1. **Delete omise, fold seller tooling into okaimono** — rejected: buyer-side and seller-side
   have genuinely different actors, lexicons, and gates (seller-gating, fulfilment, storefront
   identity); one actor doing both is the Amazon+Shopify monolith we are inverting *away* from.
2. **Keep the JSON-LD scaffold, just relabel** — rejected: it encodes the forbidden SQL read
   path and has no inversion stance; relabelling launders a violation.
3. **External-merchant marketplace (true Shopify)** — rejected: open third-party merchants with
   platform commission is external value inflow (§1.3); only SBT-gated internal sellers at R0,
   external is Lv7+-gated.

# References

- ADR-2606012100 — okaimono provisioning commons (buyer-side sibling; omise feeds Ring 1)
- ADR-2605302000 — warifu zero-fee settlement
- ADR-2605262130 — kotoba storage substrate (no RisingWave/SQL)
- ADR-2605231525 — no-server-key invariant
- Charter §1.3 (donation-only), §1.13 (anti-dark-pattern)
