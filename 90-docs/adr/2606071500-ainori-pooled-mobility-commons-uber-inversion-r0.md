---
id: adr-2606071500-ainori-pooled-mobility-commons
title: "ADR-2606071500: ainori 相乗り — pooled passenger-mobility commons (Uber charter-clean inversion), R0"
status: proposed
doc_type: adr
topic: ainori-mobility-commons
authoritative: true
last_verified: 2026-06-07
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - 20-actors/ainori
depends_on:
  - 2606042300   # todoke last-mile route core + SAE-L4 safety envelope (reused)
  - 2605242000   # wadachi autonomous-mobility R&D
  - 2606042100   # tazuna teleop / fleet control plane
  - 2605262130   # kotoba storage substrate
related:
  - 2606032130   # displacement dividend (labour coupling)
supersedes: []
superseded_by: []
---

# ADR-2606071500: ainori 相乗り — pooled passenger-mobility commons (Uber charter-clean inversion), R0

**Status**: proposed
**Date**: 2026-06-07
**Deciders**: Jun Kawasaki

# Context

The audit found mobility coverage is **goods-only**: `todoke 届け` (last-mile parcel delivery,
real Rust route core + SAE-L4 safety envelope), `wadachi 轍` (inter-site material autonomy,
scaffold), `tazuna 手綱` (fleet teleop, safety reasoner). **Passenger** mobility — the Uber /
Lyft / Grab surface — is entirely uncovered, and `todoke`'s lexicon hard-codes goods
(`payloadClass`), so passengers cannot be smuggled into it.

A faithful Uber clone is **structurally charter-forbidden**:

- Uber's core = a **gig labour-arbitrage marketplace**: piece-rate drivers matched + paid per
  trip, platform takes 25–30 %. Charter §1.13 is explicitly **anti-gig**; `todoke` already
  encodes `gig:const=false`.
- **Surge pricing** = demand-driven price discrimination, a Wellbecoming dark-pattern
  (§1.13).
- Real-time **rider tracking** = pattern-of-life surveillance, forbidden by the
  privacy-by-construction posture (`watari` G4, `todoke` G8).

The real human need — members need to move; a member with a vehicle is already going that way —
is mission-aligned and, in its *pooled* form (相乗り = ride-sharing/carpool, the classic
乗合 communal-transport tradition), is **anti-individualist by construction**: it maximizes
occupancy of trips that are happening anyway rather than inducing solo-hail demand.

# Decision

Introduce **`ainori 相乗り`** (Tier-B actor, `ainori.etzhayyim.com`), a **pooled
passenger-mobility commons**, R0 design + scaffold, that **reuses `todoke`'s route core** (NN +
2-opt sequencing, SAE-L4 refusal-not-clamp safety envelope) for multi-stop pooled routing.

**Inversions (gates, see manifest):**

| Uber term | ainori charter-clean dual | gate |
|---|---|---|
| gig driver, piece-rate | member contribution; cost-share + **displacement-dividend** coupling, `cash≡0` for the platform | G1 no-gig |
| surge / dynamic price | flat **cost-share** split across pooled riders (fuel/energy + wear, no margin) | G2 no-surge |
| solo-hail maximization | **pooling-first**: occupancy/commons maximized, solo trips deprioritized | G11 anti-individualism |
| real-time rider tracking | on-device, ephemeral; **no pattern-of-life**, no person-tracking datoms | G7 / G12 privacy |
| platform-held payment credential | member signs each settlement (ERC-4337/passkey); server holds no key | G5 no-server-key |
| human + autonomous blurred safety | SAE-L4 ceiling, per-zone speed caps **enforced by refusal** (reuse todoke envelope) | G3 safety-envelope |

**Two supply modes (both non-gig):**
1. **Human-pooled** — a member already driving a route offers seats; riders cost-share; the
   driver is never *paid* (contribution → vocation → dividend), only fuel/wear is split.
2. **Autonomous-pooled** — `wadachi`/`tazuna` SAE-L4 shuttle on fixed/semi-fixed loops; live
   operation Council Lv6+ + operator gated.

**Scope at R0:** lexicons + manifest + kotoba schema + cell scaffolds (`pool_match` langgraph,
`route_sequence` reusing `todoke-route`, `safety_envelope`, `settle`) + bounded
`:representative` seed. **No live dispatch, no live actuation** (G10, gated). Settlement
intent-only until warifu Phase-2.

# Consequences

- Closes the passenger-mobility gap without creating a gig marketplace (no piece-rate, no
  surge, no driver-payment field exists in any lexicon).
- Reuses the proven `todoke` route core + safety envelope — net-new code is the pooled-matching
  cell + cost-share settlement, not a second routing engine.
- Adds one Tier-B actor to the roster index + Status table; couples to the displacement-dividend
  ladder (ADR-2606032130).

# Alternatives Considered

1. **Extend `todoke` to carry passengers** — rejected: `todoke`'s lexicon and safety envelope
   are goods/curb-to-door specific; passenger consent, occupancy, and habitability semantics
   differ. Sibling actor sharing the route *crate* is cleaner than overloading the lexicon.
2. **Faithful Uber with non-profit driver payouts** — rejected: still a piece-rate gig model
   (§1.13 violation); "non-profit payout" is payroll the charter excludes (no-payroll invariant).
3. **Autonomous-only (skip human-pooled)** — rejected: human-pooled is shippable now and is the
   anti-individualist 乗合 core; autonomous is the maturation path, not the entry point.

# References

- ADR-2606042300 — todoke last-mile route core + SAE-L4 envelope (reused crate)
- ADR-2605242000 — wadachi autonomous-mobility R&D
- ADR-2606042100 — tazuna teleop / fleet control plane
- ADR-2606032130 — displacement dividend (labour coupling)
- Charter §1.13 (anti-gig, anti-dark-pattern, no-payroll)
