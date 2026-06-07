---
id: adr-2606072800-tsubasa-flight-discovery-commons
title: "ADR-2606072800: tsubasa 翼 — flight-route/fare discovery commons (Skyscanner inversion), R0+R1"
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

# ADR-2606072800: tsubasa 翼 — flight-route/fare discovery commons (Skyscanner inversion), R0+R1

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
stripped self-book handoff over a bounded `:representative` fare set. Live GDS/airline fare ingest
is **Council Lv7+ + operator gated** (G8) — R0 ships representative data only; no real booking is
transacted by tsubasa (member self-books).

**Composition:** sibling of `watari` (position) — tsubasa is the *planning* layer, watari the
*live* layer; both are observational, neither is an OTA. Emissions data composes with the
Wellbecoming carbon axis used by okaimono.

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
