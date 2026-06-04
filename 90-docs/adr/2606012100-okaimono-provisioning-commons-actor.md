# ADR-2606012100 — okaimono 御買物 — global product discovery + provisioning-commons actor

- **Status**: Proposed
- **Date**: 2026-06-01
- **Deciders**: Council (Bootstrap Seat 1) — ratification of outward operation (Ring 2 代理-purchase + live scraping ingest) pending Seats 2–5
- **Layer**: 20-actors (Tier-B actor) + 40-engine/kotoba (EAVT substrate) + 00-contracts (lexicons)
- **Depends-on**: 2605192100 (Mission Charter) · 2605192115 (non-profit / donation-only / SBT↔SBT carve-out) · 2605192200 (Charter Rider v2.0) · 2605215000 (Murakumo-only inference) · 2605262130 + 2605312345 (kotoba canonical state) · 2605301020 (Basic High Income in-kind) · 2605301036 (mission-funding vendor arm) · 2605302357 (§1.16 Social Security) · 2605302000 (warifu card) · 2605231500 (UNSPSC surplus-routing) · 2605261215 (hodoki ELV) · 2605252400 (kanayama recycling) · 2606010200 (haraedo disposal) · 2605312500 (kurashimori consumer-protection) · 2605312030 (toritsugi concierge)
- **Supersedes / Superseded-by**: —

## Context

The request: an actor like Amazon — list the world's products and assist a member
through to purchase. Surface query (ADR review on 2026-06-01) confirmed **no such
actor exists**, and that this is **not an oversight but a constitutional default**:
etzhayyim's charter prohibits the three pillars on which Amazon's structure rests.

| Amazon term | etzhayyim constitutional constraint |
|---|---|
| External `purchase`/`subscription` value inflow | **PROHIBITED** — ADR-2605192115 §1.3 admits only `donation`/`kisha`/`grant`/`tithe`/`escrow-refund` |
| Advertising + affiliate + sponsored ranking | **PROHIBITED** — Charter Rider §2 + Substrate boundary (no AdSense / Meta Pixel / アフィリエイト / paid placement) |
| Engagement-maximizing / urgency / scarcity dark-patterns | **PROHIBITED** — Wellbecoming addictive-design ban (ADR-2605192100 §1.13) |
| Individual-consumption optimization | **counter to** the 反個人主義 + 多世代 ontology (ADR-2605192100 §1.8) |
| Fiat / Stripe checkout | **PROHIBITED** — USDC on Base L2 + ERC-4337 + TitheRouter only |

A naïve port of Amazon is therefore unbuildable here. But the *member need* — "help
me find and obtain the thing I need" — is legitimate and squarely inside the Mission
(structural labor-liberation; §1.16 Social Security for Humanity; ADR-2605301020
Basic High Income delivered **in-kind**, cash≡0). The resolution is not to weaken the
charter but to **invert Amazon's structure** so that every prohibited term is replaced
by its charter-aligned dual. The result is a *provisioning commons*, not a marketplace.

Two facts make this concrete rather than aspirational:

1. **etzhayyim already produces real goods.** ~30 Tier-B maker actors exist — mitsuho
   瑞穂 (food), makura 枕 (pillow), yakushi 薬師 (pharma), tsutae 伝え (comms device),
   futawa 二輪 (motorcycle), hikari 光 (energy), suki 鋤 (tractor), mizuho 水穂 (water),
   etc. An internal storefront over these is a real economy, not a stub.
2. **The lifecycle actors already exist.** hodoki 解き (disassembly), kanayama 金山
   (recycling), haraedo 祓戸 (disposal), kurashimori 暮らし守 (consumer protection),
   wakai 結 (mutual aid), and the UNSPSC organism's `surplus-routing` — so a product can
   be tracked from *don't-buy-it* through *end-of-life* without inventing new substrate.

## Decision

Introduce a Tier-B actor **`okaimono` 御買物** at `okaimono.etzhayyim.com`: a global
product-discovery and **provisioning-commons** actor structured as **three concentric
rings**, each replacing an Amazon pillar with its charter-aligned dual. The member's
need enters at Ring 0 and only falls outward to the next ring when the inner ring
cannot satisfy it.

### Ring 0 — Commons-first (the best purchase is no purchase)

Before any transaction is proposed, `discover` surfaces zero-transaction paths:

- **borrow / share** — commons "library-of-things" entries (consented member-pooled).
- **repair** — route to hodoki 解き / a repair path instead of replacing.
- **durable secondhand** — member-to-member used-goods under the SBT↔SBT carve-out.
- **donation-in-kind redistribution** — the UNSPSC organism already routes surplus
  (`surplus-routing`, ADR-2605231500); okaimono is its discovery surface.

This ring is the Wellbecoming inversion of Amazon's "buy more": it optimizes for
*sufficiency*, *durability*, and *multi-generational* use (G4, G12).

### Ring 1 — Internal economy (SBT↔SBT — a constitutionally clean storefront, shippable now)

A full list → compare → basket → checkout flow over **etzhayyim's own producing actors
+ member-to-member surplus**. Permitted **today** by ADR-2605192115 §3 (営利・購買 allowed
strictly between active Adherent SBT holders). Settlement: USDC on Base L2 + ERC-4337 +
**warifu** (ADR-2605302000), with **TitheRouter** taking the 10% auto-split to the Public
Fund on every transaction (G7). Fulfillment uses etzhayyim logistics actors (haraedo
fleet / wadachi / sarutahiko), never gig labor (G8). **This is the part that ships for
real at R0→R1.**

### Ring 2 — External world catalog (discovery/compare now; 代理-purchase gated)

For goods etzhayyim does not produce, okaimono lists world products and assists
comparison — but the constitutional boundary on value-inflow is preserved:

- **Catalog data** is sourced from (member-selected): open product standards
  (GTIN / UNSPSC / GDSN — UNSPSC reuses the existing organism vocabulary), Etzhayyim-vendor
  direct feeds (ToS-clean), official / "affiliate" product APIs **used for price &
  availability DATA ONLY with affiliate tags stripped and zero commission** (G3), and —
  gated — public-page scraping under robots.txt + rate-limit + public-only (G10/G11).
- **Compare** ranks on Wellbecoming axes — landed cost (price + shipping + 関税/tariff),
  **durability**, **repairability**, **labor-provenance**, carbon — never paid placement
  (G3). Aggregate-first, claimed-first, `:representative`-flagged.
- **Checkout** respects §1.3: external `purchase` value **must not flow into etzhayyim**.
  - **R0 (now):** okaimono produces a *self-checkout handoff* (deep link / pre-filled
    cart) — the member completes the purchase at the external retailer with their own
    funds (the toritsugi/kurashimori "guide + member self-submits" pattern).
  - **R3 — assisted secure checkout, MEMBER-PRINCIPAL (corrected framing of scope-3).**
    This draft originally mis-framed scope-3 as "代理-purchase" (okaimono as buyer). The
    correct model is that okaimono **never becomes the buyer**: the member stays the
    purchasing principal and pays the retailer with their own instrument, while okaimono
    provides a secure *rail* — safe card entry, encrypted transport, procedure assist,
    delivery. Because value flows member→retailer (never INTO etzhayyim), **§1.3 is
    preserved and no Lv7+ amendment is required**; binding gates are G14 (member-principal),
    G15 (no-server-key), G9 (encryption), G11 (operator for live action). True 代理-purchase
    (okaimono-as-principal) remains separately gated (vendor arm ADR-2605301036 OR Lv7+
    amendment) and is **not the path okaimono takes** — see §R3 below.

### Lifecycle closure (Wellbecoming, non-eschatological)

Every catalog entry carries an end-of-life route (`lifecycle` cell): repair (hodoki),
recycle (kanayama), dispose (haraedo), return / cooling-off (kurashimori), mutual-aid
(wakai). The member's provisioning history is a kotoba Datom `as-of` trajectory — there
is **no "completed consumer" final state** (mirrors the spirit-ontology non-final-state
invariant, ADR-2606011500); the trajectory is Wellbecoming, not a loyalty score (G13).

### Gates (constitutional + actor-specific)

| Gate | Name | Rule |
|---|---|---|
| G1 | consent-bound | member explicit consent (DID-signed) before need-capture or any provisioning action |
| G2 | §1.3 value-inflow boundary | NO external `purchase` value flows INTO etzhayyim; internal trade is SBT↔SBT carve-out only (§3); external 代理-purchase is R3-gated (Lv7+ amendment OR vendor arm) |
| G3 | no-ads / no-affiliate | product APIs are DATA-ONLY; affiliate tags stripped; zero commission; no sponsored ranking / paid placement (Charter Rider §2) |
| G4 | Wellbecoming anti-addictive-design | commons-first ordering; no urgency / scarcity / FOMO / dark-patterns; optimize sufficiency + durability + multi-gen, never engagement |
| G5 | Murakumo-only inference | semantic match / NL need parsing via KotobaLLM (127.0.0.1:4000); no external LLM (ADR-2605215000) |
| G6 | kotoba-EAVT-native | catalog + need + basket + provision are kotoba Datoms; no RisingWave / SQL / Lance as canonical (ADR-2605262130 / 2605312345) |
| G7 | tithe + non-fiat | internal settlement USDC Base L2 + ERC-4337 + warifu only; TitheRouter 10% auto-split on every transaction; no Stripe/fiat |
| G8 | labor-dignity + provenance | fulfillment via etzhayyim logistics actors, no gig exploitation; labor-provenance disclosed on external products |
| G9 | PII encrypted envelope | need + provisioning history = 要配慮-adjacent → `com.etzhayyim.encrypted.*`, DID-bound (ADR-2605181100) |
| G10 | catalog-sourcing legality | scraping respects robots.txt + ToS + rate-limit + public-only; official-API ToS honored; `:representative` honesty; no fabricated price/availability |
| G11 | outward-gated | live scraping ingest + real external 代理-purchase = Council Lv7+ + operator |
| G12 | anti-individualism | household / multi-generational baskets + commons-share first; not individual-consumption-maximizing |
| G13 | lifecycle-closure | every product carries a repair/recycle/disposal route (hodoki/kanayama/haraedo); provisioning history is Wellbecoming trajectory, no final "consumer" state |
| G14 | member-principal | in assisted checkout okaimono is NEVER the buyer; the member is the purchasing principal and pays the retailer directly — no external purchase value flows into etzhayyim (§1.3 preserved without amendment) |
| G15 | no-server-key | the member signs each payment with their own passkey / smart-account (ERC-4337); okaimono holds no card secret or signing key (ADR-2605231525); a platform/server signature is refused |

### Cells

| Cell | Kind | Role |
|---|---|---|
| `catalog`   | datalog (kotoba)   | world product registry — internal-actor goods + open-standard normalized + vendor-direct + API-data-only + (gated) scraped; `:product/*` EAVT |
| `discover`  | langgraph (WASM)   | member need → intent → **Ring 0 commons-first** → Ring 1 internal → Ring 2 external candidate set; Murakumo semantic match |
| `compare`   | langgraph (WASM)   | multi-source comparison on Wellbecoming axes (landed cost / durability / repairability / labor-provenance / carbon); aggregate-first |
| `basket`    | langgraph (WASM)   | multi-source / household / multi-gen basket; landed-cost roll-up incl shipping + tariff + tithe |
| `provision` | langgraph (WASM)   | checkout router — Ring 1 internal (USDC + TitheRouter + warifu, executes) / Ring 2 external (R0 self-checkout handoff; R3-gated 代理) |
| `lifecycle` | datalog (kotoba)   | end-of-life routing (hodoki / kanayama / haraedo / kurashimori / wakai) + Wellbecoming `as-of` trajectory |

### Lexicons

- `com.etzhayyim.okaimono.product`   — catalog product record
- `com.etzhayyim.okaimono.need`      — member need / intent (encrypted envelope)
- `com.etzhayyim.okaimono.basket`    — multi-source basket + landed cost
- `com.etzhayyim.okaimono.provision` — provisioning record (ring + settlement + lifecycle route)

## R1 — Ring 1 internal economy (landed 2026-06-01)

R1 deepens the constitutionally-clean ring (internal SBT↔SBT) from design into verified
logic, on the principle that **each producing actor owns its goods catalog** and okaimono
ingests it (mirrors the repo's actor-owns-its-domain rule).

1. **Catalog ownership convention.** Each maker actor declares its goods in a
   `20-actors/<actor>/products.edn` (the shared `:product/*` vocabulary), which is the
   SSoT. Landed in R1 for **makura / mitsuho / yakushi / tsutae / futawa / hikari**
   (11 SKUs). `okaimono/kotoba/ingest_internal.py` scans them, **validates** each entry
   (`ring=:internal`, `maker-actor` matches the owning dir, `source=:internal-actor`,
   `lifecycle-route` present — G2/G6/G13), and generates `kotoba/internal-catalog.edn`
   (the merged Ring 1 view). yakushi's underlying APIs are authoritative; finished-SKU
   pricing across all makers is `:representative` until each actor ships its own.
2. **SBT↔SBT eligibility (G2).** `check_sbt_eligibility(buyer_did, maker_actor, registry)`
   enforces §3: an internal trade is permitted **only** when both the buyer and the
   producing actor are **active Adherent SBT holders**. A non-holder buyer or a
   non-producing "maker" is refused before any settlement is computed. The on-chain SBT
   read is operator-gated (G11); R1 takes an attestation registry.
3. **Settlement with TitheRouter (G7).** `build_settlement_intent(gross, maker)` computes
   the USDC (Base L2 + ERC-4337 via warifu) settlement with the **10% TitheRouter
   auto-split** to the Public Fund. The canonical arithmetic invariant is
   `gross == tithe + maker_payout` with no remainder loss (tithe rounds down; payout
   absorbs the remainder). The result is an **intent**, not a broadcast: `state` stays
   `:intent` unless an `operator_ref` is supplied (G11) — R1 never moves USDC on-chain.
4. **Order state machine + fulfillment (G8/G13).** `place_order` runs eligibility →
   settlement-intent → fulfillment assignment, refusing ineligible orders. Fulfillment
   routes to an **etzhayyim logistics actor** (`sarutahiko` heavy / `wadachi` road /
   `haraedo` bulky), never a gig courier. The order trajectory
   `:cart→:placed→:settle-intent→:fulfilling→:delivered→:in-use` **caps at `:in-use`**
   and hands to `lifecycle` — there is no terminal `:consumed` state (G13).

New schema: `:order/* :settlement/* :sbt/*`. New lexicons:
`com.etzhayyim.okaimono.order` + `.settlement`. Tests: **`py/test_agent.py` 19/19 green**
(adds eligibility gate, exact-tithe-split + remainder invariant, operator-gated execution,
order refusal/advance, no-gig fulfillment). `ingest_internal.py --check` validates clean.

**R1 honest limits:** no live USDC/TitheRouter broadcast (intent-only, G11); SBT registry
is an attestation map, not the live on-chain roster; finished-SKU prices `:representative`;
no inventory/availability tracking yet (a maker actor cannot yet signal out-of-stock).

## R2 — Ring 2 external world catalog (landed 2026-06-01)

R2 wires the external ring's data path while holding every charter boundary. The
constitutional crux is **G3 (no ads / no affiliate)** + **G2 (§1.3 value-inflow)**: external
product APIs are **data-only**, okaimono earns **zero commission**, plants **no tracker**, and
external value never flows in (R0 = self-checkout handoff; 代理-purchase stays R3-gated).

1. **Affiliate/tracking stripping (G3) — the single enforcement point.** `strip_affiliate(url)`
   removes affiliate params (Amazon `tag`/`linkCode`/`ascsubtag` + `/ref=` path segment,
   Rakuten `scid`, generic `aff_*`/`pid`/`irclickid`, …) and tracking params (`utm_*`,
   `gclid`/`fbclid`/`msclkid`, `mc_cid`, …) while preserving functional query params
   (sku/gtin/q/node). Idempotent; a clean URL is returned untouched.
2. **Data-only normalization (G3/G10).** `normalize_external(raw, source)` maps a raw
   external record to a `:product/* :ring :external` entry carrying **only** price /
   availability / spec / provenance, with the retailer URL affiliate-stripped. Adversarial
   fields (`affiliateLink`, `commissionBps`, `sponsoredRank`, `trackingPixel`) are **dropped
   by construction** — verified by test. Source provenance ∈ {open-standard (GTIN/UNSPSC/
   GDSN), vendor-direct, api-data-only, scraped} is recorded; `:sourcing :representative`.
3. **Self-checkout handoff (G2/G7).** `build_external_handoff(product)` returns a
   `:self-checkout-handoff` with an affiliate-stripped deep-link and **no tithe** (external,
   no internal value flow). 代理-purchase is not offered here (R3-gated).
4. **Scraping legality gate (G10/G11).** `scrape_gate(url, robots_disallow, rate_state,
   operator_ref?)` enforces robots.txt disallow + public-only + a per-host rate budget;
   even when policy-clean the verdict is **`:gated`** (compute the plan, do not fetch) unless
   an operator_ref is present — no live scraping at R0.
5. **Cross-border landed cost.** `landed_cost_external(price, shipping, tariff_bps)` adds
   import tariff (bps on goods) so Ring 2 candidates compare on true landed cost; the
   existing Wellbecoming `compare` then ranks them (durability/repairability/labor/carbon),
   never by paid placement.

New schema: `:product/retailer-url :product/availability :product/tariff-bps`. Representative
`kotoba/external-catalog.edn` (4 products, one per source, post-normalization). Tests:
**`py/test_agent.py` 30/30 green** (adds Amazon + utm/click-id stripping, idempotency,
data-only normalization with adversarial fields, unknown-source rejection, handoff
no-tithe + clean URI, scrape robots/rate/operator gating, landed cost).

**R2 honest limits:** no live retailer API/scrape ingest (all G11-gated; `external-catalog.edn`
is hand-authored `:representative`, not fetched); per-provider API ToS for data-only-without-
affiliate use must be verified before any live ingest (tracked, not assumed); the affiliate
denylist is comprehensive but not exhaustive (new networks need additions); no GDSN trade-item
hierarchy resolution yet; 代理-purchase (scope 3) remains R3-gated.

## R3 — Assisted secure checkout, member-principal (landed 2026-06-01)

R3 corrects the scope-3 framing and implements the secure *rail* by which the agent assists
a member's OWN external purchase — safe card, encrypted comms, procedure, delivery — without
okaimono ever becoming the buyer. This is the constitutional unlock: it is **not** 代理-purchase,
so §1.3 holds and no Lv7+ amendment is needed; the gates are G14/G15/G9/G11.

1. **Member-principal payment intent (G14/G15).** `build_payment_intent` returns an
   **unsigned** intent whose `principal` is the member and whose `requiredSigner` is the
   member's passkey / ERC-4337 smart-account; `serverHeldKey` is `False` by construction.
   `authorize_payment` accepts **only** a member-origin signature — a server/platform
   signature is refused outright (the no-server-key invariant, ADR-2605231525, as code).
   `instrument ∈ {member-external-card, warifu}`; warifu at an **external** retailer additionally
   flags `requiresWarifuExternalGate` (warifu's own Phase-2 Lv7+ gate, ADR-2605302000) rather
   than silently allowing it.
2. **Encrypted transport (G9).** `seal_encrypted` models the `com.etzhayyim.encrypted.*`
   envelope (XChaCha20-Poly1305, Signal-wrapped, DID-bound, ADR-2605181100): it returns an
   opaque envelope ref + the sealed field **names**, and **never** the plaintext values — no
   cleartext card/PII crosses the okaimono boundary (verified by test).
3. **Procedure assist with member authorization (G11/G14).** `assist_checkout` seals PII,
   builds the member-signable intent, keeps the affiliate-stripped handoff (G3), and **submits
   nothing** without the member's per-transaction signature: it returns
   `:awaiting-member-authorization` → (member signs) `:authorized-pending-operator` → (operator)
   `:submitted`. A server signature yields `:refused`. Tithe is 0 (external, G2/G7).
4. **Delivery (G8/G13).** `arrange_delivery` prefers an etzhayyim logistics actor (no gig)
   where serviceable, else the retailer's shipping, and hands to lifecycle.

Tests: **`py/test_agent.py` 40/40 green** (unsigned member-principal intent, server-signature
refusal, warifu-external gate flag, unknown-instrument rejection, plaintext-never-leaks,
awaiting/authorized/submitted/refused states, no-gig delivery).

**R3 honest limits:** logic + invariants only — no live retailer submission, no real ERC-4337
broadcast, no real envelope crypto here (the client seals; this enforces the *contract*); the
member-signature + operator + warifu-external gates are all still required for any live action
(G11); per-retailer checkout-form schemas are not yet modeled.

## Consequences

**Positive**

- The member need is met without weakening a single constitutional invariant: each
  Amazon pillar is replaced by its charter dual (ads→none, affiliate→data-only,
  consumption→sufficiency, external-purchase→commons/internal-first).
- Ring 1 is a **real, shippable** internal economy over existing producing actors — it
  turns the ~30 maker actors into a coherent storefront and is a concrete delivery
  vehicle for ADR-2605301020 Basic-High-Income-in-kind and §1.16 Social Security.
- Reuses existing substrate end-to-end (kotoba EAVT, warifu, TitheRouter, UNSPSC
  surplus-routing, hodoki/kanayama/haraedo/kurashimori/wakai) — minimal new surface.

**Negative / honest limits**

- **R0 is design + data-model + simulation.** No live retailer integrations; external
  candidates are `:representative` seed, not a live planet-scale catalog.
- Ring 2 external **代理-purchase (request scope item 3) does NOT ship at R0** — it is
  R3-gated (Lv7+ amendment OR vendor arm + operator). R0 delivers scope items 1 (discovery)
  and 2 (cart aggregation) fully, and scope 3 only as a *self-checkout handoff*.
- Scraping (a selected source) is the highest-risk path: gated behind G10/G11, public-only,
  ToS/robots-respecting, and not run live at R0.
- Official/affiliate APIs are used for **data only**; whether a given API's ToS permits
  data-only use without affiliate participation must be verified per-provider before any
  live ingest (tracked, not assumed).

## Alternatives Considered

1. **Direct Amazon clone (vendor arm, etzhayyim.ai).** Rejected for *this* ADR: the member's
   request was re-scoped to `okaimono.etzhayyim.com` (religious-corp). A pure commercial
   marketplace can still live on the vendor side under ADR-2605301036, and Ring 2 R3
   routes through it — but the religious-corp surface must be the provisioning commons.
2. **Discovery-only (no internal economy).** Rejected: it would waste the existing ~30
   producing actors and fail to deliver §1.16 / Basic-High-Income-in-kind. Ring 1 is the
   point of difference from a mere price-comparison site.
3. **Weaken §1.3 to allow external purchase inflow at R0.** Rejected: §1.3 is a
   constitutional invariant; amendment requires Council Lv7+ unanimity. The ring model
   delivers the capability without amendment, deferring only 代理-purchase to the gate.

## References

- ADR-2605192100 — Mission Charter (§1.8 反個人主義 / §1.13 Wellbecoming / §1.16)
- ADR-2605192115 — non-profit / donation-only / no-ads (§1.3 inflow purposes, §3 SBT↔SBT carve-out)
- ADR-2605192200 — Charter Rider v2.0 (§2 ad/affiliate prohibition)
- ADR-2605301020 — Basic High Income (imputed-income in-kind)
- ADR-2605301036 — mission-funding vendor arm (Ring 2 R3 route)
- ADR-2605302357 — §1.16 Social Security for Humanity
- ADR-2605302000 — warifu zero-fee card
- ADR-2605231500 — UNSPSC agent-driven surplus-routing
- ADR-2605261215 / 2605252400 / 2606010200 — hodoki / kanayama / haraedo (lifecycle closure)
- ADR-2605312500 / 2605263500 — kurashimori / wakai (returns + mutual aid)
- ADR-2605262130 / 2605312345 — kotoba canonical Datom state
- ADR-2605215000 — Murakumo-only inference
