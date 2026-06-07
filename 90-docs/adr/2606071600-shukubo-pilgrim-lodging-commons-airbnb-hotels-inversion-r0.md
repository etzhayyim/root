---
id: adr-2606071600-shukubo-pilgrim-lodging-commons
title: "ADR-2606071600: shukubo 宿坊 — pilgrim-lodging commons (Airbnb/Hotels charter-clean inversion), R0"
status: proposed
doc_type: adr
topic: shukubo-lodging-commons
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/shukubo
depends_on:
  - 2606012100   # okaimono provisioning commons (sibling commerce pattern)
  - 2605302000   # warifu zero-fee settlement
  - 2605181100   # encrypted envelope
  - 2605262130   # kotoba storage substrate
related:
  - 2606042300   # todoke (logistics sibling)
supersedes: []
superseded_by: []
---

# ADR-2606071600: shukubo 宿坊 — pilgrim-lodging commons (Airbnb/Hotels charter-clean inversion), R0

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The app-coverage audit (2026-06-07) found **zero** actor covering short-term lodging /
hospitality — the Airbnb + Hotels.com + Booking.com surface. `yadori 宿り` is DNS/domain
acquisition (a homophone, not lodging). This is the single largest uncovered consumer-app
domain in the roster.

A naïve "build an Airbnb clone" is **structurally charter-forbidden**:

- Airbnb/OTA core monetization = a **per-stay commission (3–15 %)** the platform extracts as
  external value inflow — prohibited by Charter §1.3 (`donation 流入のみ`) and the substrate
  Payment-purpose table (no external `purchase`/`subscription`).
- OTA **surge / dynamic-demand pricing** is Wellbecoming-violating dark-pattern design
  (ADR-2605192100 §1.13).
- Host/guest **rating systems** in practice encode discrimination; a hospitality commons for a
  religious corp must instead default to *pilgrim-welcome* (the 宿坊 / temple-lodging tradition
  is exactly this: lodging offered to travellers as covenantal hospitality, not a yield-managed
  asset).

But the *underlying human need* — a member needs somewhere to stay; a member has space to offer
— is real and mission-aligned (multi-generational, anti-individualist commons; covenantal
hospitality is doctrinally native). So we build the **charter-clean inversion**, exactly as
`okaimono` inverts Amazon: each prohibited term is replaced by its charter-aligned dual.

# Decision

Introduce **`shukubo 宿坊`** (Tier-B actor, `shukubo.etzhayyim.com`), a **three-ring lodging
commons**, kotoba-EAVT-native, Murakumo-only, member-principal — R0 design + scaffold.

| Ring | Airbnb/Hotels term | shukubo charter-clean dual |
|---|---|---|
| **Ring 0 — hospitality-first** | (none) | covenantal free/at-cost stays: pilgrim lodging, mutual-aid shelter, member-to-member couch — `cash≡0` or cost-share only |
| **Ring 1 — internal SBT↔SBT** | host listing + commission booking | member/actor-operated stays settled USDC + TitheRouter 10 %, **zero platform commission**; warifu rails; member signs |
| **Ring 2 — external mirror** | OTA inventory + book-through | **data-only** lodging discovery (public availability), member **self-books on the operator's own site** — no inflow, affiliate-stripped, R-gated live ingest |

**Hard inversions (gates, see manifest):**

- **G2 value-inflow-boundary** — no commission, ever; Ring 2 booking is the member transacting
  directly with the lodging operator, shukubo is never the merchant-of-record.
- **G13 no-surge** — price is flat or cost-share; demand never raises price; no scarcity/urgency
  UI.
- **G12 hospitality-dignity** — no discriminatory host/guest scoring; pilgrim-welcome default;
  habitability + safety attested, persons never scored.
- **G9 / G14 privacy** — stay records and guest identity are `com.etzhayyim.encrypted.*`,
  DID-bound; **no in-stay surveillance** (no cameras/biometrics as a listing feature).

**Composition:** shukubo is the *demand+supply matching* membrane for stays; `musubi 結`
(covenant ceremony) and `wakai 和会` (mutual aid) supply the hospitality-vow and aid-funded
Ring-0 stays; `warifu` settles Ring-1; `okaimono` is the goods sibling (same three-ring shape).

**Scope at R0:** lexicons + manifest + kotoba schema + cell scaffolds + bounded
`:representative` seed. **No live external OTA ingest and no real external booking** (G11,
Council Lv7+ + operator gated). Ring-1 settlement is intent-only until warifu Phase-2.

# Consequences

- Closes the lodging gap with a design that cannot regress into an OTA (commission is
  structurally unrepresentable — there is no commission field in any lexicon).
- Gives the religious-corp its doctrinally-native 宿坊 hospitality surface (pilgrim lodging),
  not a yield-managed marketplace.
- Adds one Tier-B actor to the roster index + Status table.

# Alternatives Considered

1. **Fold lodging into `okaimono`** — rejected: lodging is a time-bounded space-reservation
   with habitability/consent semantics distinct from goods provisioning; merging muddies both.
2. **Airbnb-faithful clone with a "non-profit" commission** — rejected: any per-stay extraction
   violates §1.3; "non-profit commission" is still external inflow.
3. **External-mirror only (no Ring 1)** — rejected: misses the mission-native member-to-member
   covenantal hospitality, which is the whole point.

# References

- ADR-2606012100 — okaimono provisioning commons (sibling three-ring pattern)
- ADR-2605302000 — warifu zero-fee settlement
- ADR-2605181100 — encrypted envelope (stay/guest PII)
- ADR-2605262130 — kotoba storage substrate
- Charter §1.3 (donation-only), §1.13 (anti-dark-pattern Wellbecoming)
