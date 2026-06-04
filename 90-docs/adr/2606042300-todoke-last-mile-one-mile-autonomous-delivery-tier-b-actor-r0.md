---
id: adr-2606042300
title: "todoke 届け — last-mile (one-mile) autonomous delivery Tier-B actor (R0)"
status: proposed
doc_type: adr
topic: last-mile-one-mile-autonomous-delivery
authoritative: true
last_verified: 2026-06-04
priority: 5.0
axis: architecture
weight: 0.70
priority_note: ""
authoritative_for:
  - todoke (届け) last-mile ("one-mile") autonomous-delivery actor charter (R0)
  - curb-to-door small-payload delivery ODD + SAE-L4 sidewalk safety envelope
  - the todoke-route Rust core (stop sequencing + safety envelope) + its Python parity mirror
depends_on:
  - ADR-2605192100 (Mission Charter — §1.12 Transparent Force three-condition invariant)
  - ADR-2606010600 (kami-autodrive GNC — the perception/planning/control engine todoke consumes)
  - ADR-2605242000 (wadachi — inter-site ground autonomy; todoke is its last-metre sibling)
  - ADR-2605231525 (no-server-key — recipient signs the hand-off, server never does)
  - ADR-2606032130 (Displacement Dividend — the G2 coupling gate for freed couriers)
  - ADR-2605215000 (Murakumo-only inference)
related:
  - adr-2606012100
  - adr-2606010200
  - adr-2606013100
  - adr-2606032100
  - adr-2606042100
  - adr-2606033600
supersedes: []
superseded_by: []
---

# ADR-2606042300: todoke 届け — last-mile (one-mile) autonomous delivery Tier-B actor (R0)

**Status**: proposed
**Date**: 2026-06-04
**Deciders**: Jun Kawasaki

# Context

The etzhayyim transport stack moves things *between sites* and *in bulk* but never the last
metre to a person:

- **wadachi 轍** (ADR-2605242000) — inter-site ground autonomy, SAE L4 ceiling, ≤30 km/h.
- **sarutahiko 猿田彦** (ADR-2605252500/2606013100) — Class-8 trucks + the F10 LoaderRobot.
- **funadaiku 船大工** (ADR-2606013400) — zero-emission autonomous cargo ships.
- **haraedo 祓戸** (ADR-2606010200) — bulky-waste dispatch/VRP (logistics, not autonomy).
- **kami-autodrive** (ADR-2606010600) — the real Rust GNC engine (perception→plan→control,
  VehicleClass Car/Ship/Drone/Aircraft, 74 tests green) — but no actor drove the **one mile
  from the curb to the recipient's door**.

A survey for "last-mile / one-mile / ラストワンマイル / sidewalk delivery robot" found **no actor**.
This is also the part of transport most captured by the **gig economy** — piece-rate couriers,
the exact toil the labour-liberation mission exists to end. So the gap is both a technical one
(curb-to-door autonomy) and a constitutional one (the no-gig inversion of courier exploitation).

# Decision

Create **todoke 届け** ("to deliver / to reach the destination"), a Tier-B actor for **last-mile
("one-mile") autonomous delivery**: curb-to-door, small payload (≤25 kg), SAE J3016 **Level 4
ceiling**, sidewalk/pedestrian-shared ODD. todoke is the **last-metre sibling of wadachi**, the
**no-gig delivery limb of okaimono**'s provisioning commons (ADR-2606012100), and a **consumer of
the kami-autodrive GNC crate** (ADR-2606010600) — it does not re-implement perception/planning/
control; it owns only the last-mile-specific pieces.

## The Rust "one-mile" core — `todoke-route` (`20-actors/todoke/route/`)

A pure, zero-dependency, deterministic Rust crate (the repo has no root Cargo workspace, so it is
a standalone leaf crate; **`cargo test` → 7 green**). It owns exactly two things:

1. **stop sequencing** — nearest-neighbour seed + 2-opt local search over curb/door stops
   (open path, depot pinned, deterministic tie-breaks).
2. **the safety envelope (G7)** — `plan_last_mile` *refuses* (`Err(EnvelopeViolation)`) rather
   than returning a route whenever the run would (a) exceed the per-zone speed cap
   (sidewalk 1.8 / crosswalk 1.4 / door-path 1.0 / bike-lane 4.2 m/s), (b) include a stop in a
   vehicular **road** zone outside the todoke ODD (N2), or (c) assume **SAE level > 4** (N2). The
   charter is enforced *by construction*: no caller can obtain an unsafe route.

A faithful Python mirror (`methods/last_mile.py`) lets the LangGraph cell run the same algorithm
in-process; **`methods/test_last_mile.py` pins both implementations to the identical visiting
order** `[0, 4, 2, 3, 1]` on a shared fixture (one model, two runtimes — the sumitsubo pattern,
ADR-2606033600).

## 5 Pregel cells

```
parcel_intake → route_sequencing → autonomous_run → handoff_proof → telemetry_log
```

- **parcel_intake** (受付) — accept a job; refuse contraband/regulated payload classes (N3,
  e.g. pharma → yakushi cold-chain). *cell .edn at R0.*
- **route_sequencing** (順路) — `deliveryJob` → safety-validated `lastMileRoute` via the Rust
  core / Python mirror. **Fully coded + tested**; a refused envelope yields no route.
- **autonomous_run** (走行) — execute the route on kami-autodrive (Car/sidewalk variant), SAE-L4
  ceiling, emergency-stop + replan on obstacle. *cell .edn at R0; live actuation G9-gated and
  Transparent-Force bound — every actuation command an on-chain Datom (§1.12).*
- **handoff_proof** (受渡証) — on-device proof-of-delivery **and the actor's privacy spine**.
  **Fully coded + tested**: admissible proof kinds are signature / locker-code / on-device
  photo-hash only; cloud-image / face-match / biometric are unrepresentable and raise (G8/N5).
- **telemetry_log** (記録) — assemble the kotoba `missionCompleteRecord` + IPFS CID, replayable
  as-of history (非終末論). *cell .edn at R0.*

## 15 gates (G1–G15) + 6 non-goals (N1–N6)

Authoritative list in `20-actors/todoke/manifest.edn`. The load-bearing, charter-distinguishing
ones:

- **G5 no-gig / cash≡0** — todoke is the constitutional **inversion** of the gig courier: no
  piece-rate, no payroll, cash to adherents ≡ 0; contribution is vocation → donation.
- **G7 SAE-L4 sidewalk envelope** — speed/zone/level **refusal by construction** (`todoke-route`).
- **G8 privacy-by-construction** — on-device proof only; **no cloud imagery / facial recognition /
  biometric recipient ID** (the delivery robot is the opposite of a surveillance device; same
  posture as kiyome G9).
- **G2 displacement-dividend coupling** — no live courier displacement without the cohort
  registered for the tenure-weighted Displacement Dividend (ADR-2606032130).
- **G9 outward-gated + Transparent-Force bound** — live operation is Council Lv6+ + operator
  gated; R0–R1 are design + simulation only.
- **G12 no-server-key + G13 consent-bound** — the recipient signs the hand-off; no doorstep drop
  without a recorded encrypted consent reference.

Non-goals: **N1** no military/weaponized/surveillance-payload delivery · **N2** no SAE Level 5 /
no high-speed vehicular-road autonomy (that is wadachi R2+) · **N3** no regulated/contraband
payloads · **N4** no gig-labour / piece-rate model · **N5** no cloud/biometric recipient ID ·
**N6** no aerial drone delivery at R0 (ground/sidewalk first; aerial = kami-autodrive Drone class,
separately gated).

## Labour mapping

ISIC **H53** (postal & courier) · ISCO **9621** (messengers/parcel deliverers), **8322**
(drivers) · UNSPSC **78** (transportation/storage/mail).

# Consequences

**Positive**
- Closes the curb-to-door gap with a charter-clean, no-gig model and a real, tested Rust core.
- Reuses kami-autodrive rather than forking autonomy; reuses okaimono fulfilment + the
  Displacement Dividend rather than inventing parallel mechanisms.
- The G7 envelope and G8 privacy invariants are enforced in code (refusals/raises), not just prose
  — and encoded in three places (kotoba schema + lexicon `const` + state-machine guard).

**Negative / honest limitations (R0)**
- Design + logic + simulation only. **No hardware**, no live route, no live actuation.
- `todoke-route` is a 2-D metric-frame sequencer + speed/zone/level envelope — NOT a full motion
  planner (that is kami-autodrive) and NOT a certified safety system.
- The fleet (hakobi/tobira/meyasu/tedori) and seed are `:representative` (G10).
- Live operation, displacement, and settlement remain Council Lv6+ + operator gated (G9/G2/G15).

**Verification (this wave)**
- `route/`: `cargo test` → **7 green** (sequencing, 2-opt, + 4 G7 refusals).
- `methods/`: **7 green** incl. the Rust-parity test.
- `cells/`: **12 green** (route_sequencing envelope refusals + handoff_proof G8/G12/G13 guards +
  both `.solve()` RuntimeError checks). **Total 26 tests green.**

# Alternatives Considered

- **Extend wadachi instead of a new actor** — rejected: wadachi's ODD (vehicular, ≤30 km/h,
  inter-site) is a different envelope from sidewalk curb-to-door, and the no-gig/privacy/consent
  invariants are last-mile-specific. A sibling keeps each ODD and gate-set coherent.
- **Aerial drone delivery first** — rejected for R0 (N6): ground/sidewalk is the lower-risk,
  higher-coverage start; aerial reuses the kami-autodrive Drone class under a separate gate.
- **Reuse haraedo dispatch for routing** — haraedo solves multi-vehicle VRP for bulky-waste
  collection; the last mile is an open curb-to-door path with a hard safety envelope. todoke's
  `todoke-route` is the right-sized, self-contained tool; haraedo remains the fleet-dispatch layer
  above it.

# References

- `20-actors/todoke/` — actor (README, CLAUDE, manifests, cells, lex, kotoba, data, methods, route)
- `20-actors/todoke/route/src/lib.rs` — the Rust one-mile core (sequencing + G7 envelope)
- `20-actors/todoke/methods/last_mile.py` — Python parity mirror + courier liberation sizing
- ADR-2606010600 — kami-autodrive GNC (consumed engine)
- ADR-2605242000 — wadachi (inter-site sibling)
- ADR-2606012100 — okaimono (no-gig fulfilment limb)
- ADR-2606032130 — Displacement Dividend (G2 coupling)
- ADR-2605231525 — no-server-key (G12)
- ADR-2605192100 §1.12 — Transparent Force (live-actuation binding)
