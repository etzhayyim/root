---
id: adr-2606072802-tsubasa-flight-discovery-commons
renumbered_from: "2606072800"
title: "ADR-2606072802: tsubasa 翼 — flight-route/fare discovery commons (Skyscanner inversion), R0+R1"
status: proposed
doc_type: adr
topic: tsubasa-flight-commons
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/tsubasa
depends_on:
  - 2606012100   # okaimono (external-mirror + affiliate-strip pattern)
  - 2606071600   # shukubo (Ring-2 self-book handoff pattern)
  - 2605262130   # kotoba storage substrate
related:
  - 2606041827   # watari (live aircraft POSITION — sibling, different concern)
supersedes: []
superseded_by: []
---

# ADR-2606072802: tsubasa 翼 — flight-route/fare discovery commons (Skyscanner inversion), R0+R1

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The 2026-06-07 app-coverage audit named eight mainstream apps. Seven now have charter-clean
inversions (uber→ainori, airbnb/hotels→shukubo, salesforce→business-manager, calendly→yotei,
drive→organizer, indeed→talent, shopify→omise). **"Flight scanner" (Skyscanner / Google Flights)
remains the one uncovered slot** — `watari 渡り` covers live aircraft POSITION (ADS-B), not fare/
schedule search or booking.

A faithful Skyscanner is a charter conflict: it monetizes via **referral/affiliate commissions**
on every onward click, **ad placement**, and **fare-watch tracking of the user**, plus
urgency dark-patterns ("price will rise!"). The underlying need — find a flight, compare options
honestly — is fine; the inversion drops the commission, the ad, the tracking, and the urgency.

# Decision

Introduce **`tsubasa 翼`** (Tier-B actor, `tsubasa.etzhayyim.com`), a **flight-route/fare
discovery commons** — an external-data-only meta-search whose every onward link is affiliate-
stripped and where the member **self-books on the airline/operator's own site** (no inflow). It
reuses okaimono's affiliate-strip and shukubo's Ring-2 self-book-handoff patterns. R0→R1 (tested).

**Charter-clean inversions / invariants (gates, see manifest.edn):**

| Skyscanner term | tsubasa dual | gate |
|---|---|---|
| affiliate/referral commission on every click | **affiliate-stripped** onward deep-link; member books on the airline's OWN site; tsubasa is never merchant-of-record, takes no inflow | G1 no-affiliate-no-inflow |
| ad placement / sponsored fares | **data-only**; no sponsored ranking / paid placement | G2 no-ads |
| "price will rise", fare-watch nudges | **honest fares only**; no urgency/scarcity; no predictive-pressure field | G3 wellbecoming-anti-dark |
| rank by referral payout | rank by **true total cost** (fare + baggage) with **CO₂ emissions surfaced**, never hidden | G4 emissions-honest |
| fare-watch tracking of the user | **no person fare-tracking / pattern-of-life**; a search is stateless w.r.t. the searcher | G5 no-person-tracking |
| vendor pipelines / LLM | Murakumo-only; kotoba-EAVT-native | G6 murakumo-only / G7 kotoba-eavt-native |

**Scope:** R1 implements honest fare search + total-cost-with-emissions comparison + affiliate-
stripped self-book handoff over a bounded `:representative` fare set. **R2** added the observatory
+ persistence layer (per-route carrier-HHI concentration → competition reading → `:opening`;
content-addressed kotoba commit-DAG; idempotent heartbeat; DID). **R3 (2026-06-21) UNLOCKS the G8
live-ingest gate** under charter bounds (see §R3 below); no real booking is ever transacted by
tsubasa (member self-books).

**Composition:** sibling of `watari` (position) — tsubasa is the *planning* layer, watari the
*live* layer; both are observational, neither is an OTA. Emissions data composes with the
Wellbecoming carbon axis used by okaimono.

# R3 — live ingest + Murakumo digest + WASM (G8 gate UNLOCK, 2026-06-21)

**Attestation.** Per the Bootstrap operational premise (root `CLAUDE.md`, 2026-06-11: *Council
attestation = GitHub Pull Request review*), the founder (sole Council member, Lv7+, 1/1
unanimity) authorized unlocking G8. The on-record attestation is **this change's PR review +
merge** — the merge commit / PR URL is the provisional value for the `COUNCIL_*` gate reference
until the on-chain multisig (Base testnet+) supersedes it.

**What unlocks.** G8 moves from *"live ingest = Council Lv7+ gated, `:representative`-only"* to
*"live ingest operator/member-ENABLED"* — but the unlock is **charter-bounded, and the bounds are
structural (in code + tests), not policy**:

1. **No paid GDS terminal.** `ingest/assert-clean-source` accepts only `:public` (free / disclosed
   fare data) or `:member-principal` (the member's OWN airline-account API credentials). A
   `:paid-terminal` (Amadeus / Sabre / Travelport opaque billed terminal) is **refused** — an
   opaque, lock-in commercial terminal scores negative on the ECL objective function (Rider
   §2(e) specialist-knowledge / §2(i) compute lock-in; the v3.5 net-effect assessment, not a
   vendor-name ban).
2. **No-server-key.** `methods/ingest.cljc` performs **no network I/O**. The operator/member runs
   the fetch leg in their *own* runtime and hands ingest the parsed payload; the actor holds no
   key and makes no call. (Same shape as ibuki R3 / kanjō live-leg / meisai.)
3. **G1/G3/G4/G5 unchanged + enforced at ingest.** A fetched fare bearing a
   commission/affiliate/merchant/searcher/person key is **dropped** (`:reject :forbidden-key`); a
   fare with no positive CO₂ is **dropped** (`:reject :no-co2` — emissions may never be silently
   absent); the airline link is affiliate-stripped on the way in. Per-row fail-open.
4. **No booking.** tsubasa still transacts no booking; the member self-books.

Accepted fares are `:fare/sourcing :authoritative` + `:fare/source` (cited provenance) +
`:fare/ingested-at` (caller as-of), and feed the existing analyze/heartbeat/commit-DAG pipeline
unchanged.

**Murakumo digest** (`methods/digest.cljc`): a short honest paragraph over the competition/fare
map via the **loopback** Murakumo gateway (`127.0.0.1:4000`) — the host is hardcoded loopback, so
an external LLM is unrepresentable (G6); **fail-open** to a deterministic template when Murakumo is
unreachable; read-only, no-server-key. The prompt forbids urgency / "book now" / paid-recommendation
language (G3/G1).

**WASM** (`wasm/world.wit` + `build.sh`): a compute-only Component Model scaffold (`analyze` /
`coverage` / template `digest`). It imports no `wasi:sockets`/`clocks`/`random` — the *absence* is
the guarantee (G1 no-inflow / G5 no-tracking / G6 no external call); `build.sh` fails the build on
any side-effecting import or a `commission`/`affiliate` symbol. The compiled artifact + pinned CID
are the **no-server-key operator step** (shionome-core / rasen pattern); until then the actor runs
`service`-model on the bb methods and `did.json` carries `wasmCid: null`.

**Honest limit.** R3 makes the live leg *code-complete + gate-open*; the actual live pull with real
public sources / member credentials is an operator/member action (no key is held here). 54 tests /
579 assertions green, incl. the G8-bound refusal of a paid terminal and the ingest-time G1/G4/G5
rejections.

# Consequences

- Closes the last named-app coverage gap with a design that cannot become an OTA (no commission
  field is representable; booking is a self-book handoff).
- Adds one Tier-B actor; reuses proven affiliate-strip + self-book-handoff code paths.

# Alternatives Considered

1. **Extend `watari`** — rejected: watari is live-position observational (no fare/schedule/booking
   semantics); merging muddies a clean observational actor with a planning/commerce surface.
2. **Skyscanner-faithful with "non-profit" referral** — rejected: any onward commission is
   external inflow (§1.3); affiliate links are exactly what G1 strips.
3. **Fold into `kakaku`** (generic price-compare) — rejected: flights carry emissions, baggage,
   stops, and a self-book-handoff/booking-class model that the generic product comparator lacks.

# References

- ADR-2606012100 — okaimono (affiliate-strip + external-mirror pattern)
- ADR-2606071600 — shukubo (Ring-2 self-book handoff)
- ADR-2606041827 — watari (live aircraft position — sibling)
- Charter §1.3 (no external inflow), §1.13 (anti-dark-pattern Wellbecoming)
