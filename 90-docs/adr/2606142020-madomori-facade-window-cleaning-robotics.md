---
id: adr-2606142020-madomori-facade-window-cleaning-robotics
title: "ADR-2606142020: madomori 窓守 — high-rise / façade window-cleaning robotics"
status: accepted
doc_type: adr
topic: madomori-facade-window-cleaning
authoritative: true
last_verified: 2026-06-14
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Closes the HIGHEST unmet remote-value GAP named in ADR-2606073001 §4 (高所・façade window cleaning — fall fatality)."
authoritative_for:
  - high-rise / façade window-cleaning robotics actor (coverage path + wind/sway envelope + adhesion)
depends_on:
  - ADR-2606073001 (robotics remote-work coverage/GAP survey — names façade window cleaning the highest unmet remote-value GAP)
  - ADR-2606032100 (labor-liberation OSS-robotics wave — sanae/hataori/kiyome sibling pattern)
  - ADR-2606032130 (Displacement Dividend)
  - ADR-2606042100 (tazuna — teleop substrate)
  - ADR-2605215000 (Murakumo-only inference)
  - ADR-2605312345 (kotoba Datom = first-class canonical state)
related:
  - ADR-2606142000 (kuramori — the reference Clojure-first actor idiom this mirrors)
  - ADR-2606034800 (manako — on-device browser-local vision; the G3 on-device-no-cloud pattern)
supersedes: []
superseded_by: []
---

# ADR-2606142020: madomori 窓守 — high-rise / façade window-cleaning robotics

**Status**: accepted
**Date**: 2026-06-14
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

The robotics remote-work coverage survey (ADR-2606073001 §4) ranked **高所・façade window
cleaning** as the **#1 highest unmet remote-value GAP**: "fall fatality; current GAP." kiyome
清め (ADR-2606032100) is indoor/ground-level cleaning only; façade/fall-risk work was on no
roadmap. A human on a rope or in a suspended cradle, washing the glass of a high-rise, is
exactly the on-site job whose hazard (the fall) is most directly removed by putting a robot in
their place.

This ADR authors madomori (窓守 = window-keeper) to close that GAP, continuing the
**Clojure-first GAP-actor wave** opened by kuramori 倉守 (ADR-2606142000). madomori mirrors
kuramori's proven idiom exactly — pure Clojure methods (no deps) under `methods/<name>.clj`,
ns `madomori.methods.<name>`, a self-exiting `clojure.test` suite run via
`bb --classpath 20-actors`, and a kotoba EAVT Datom-log emitter (GROUND `:add` durable;
DERIVED `:derived` transient) — so the methods run under both babashka and the kotoba pywasm
runtime.

Because madomori's *raison d'être* is removing a human from the fall hazard, its safety gates
are not peripheral — they are the actor. The design makes the two fall-equivalent gates (wind
work-stop + fall-arrest redundancy, and suction adhesion factor-of-safety) **raise** rather
than soft-fail, so an unsafe descent can never be silently planned.

# Decision

Author `20-actors/madomori/` as a 🟡 R0 (design + sim) Tier-B actor.

**Methods (pure Clojure):**
1. `facade_path.clj` — façade coverage path planning over a rows×cols pane grid: a
   boustrophedon (S-shape) minimal-turn coverage sweep, total path length (m), a per-pane
   water + cleaning-agent budget (G2 — tracked so a planner minimises it), and a coverage
   completeness check (every pane visited exactly once — no skip, no double-pass).
2. `wind_envelope.clj` — a rope/BMU pendulum sway model (quasi-static deflection growing with
   wind² and rope length, shrinking with suspended mass) plus the **★ G5** safety gate:
   `work-permitted?` **RAISES** at/above the wind work-stop threshold (≈10 m/s; not tunable up
   by a planner; gusts checked too) and **RAISES** with fewer than 2 independent fall-arrest
   anchors (a single-anchor descent is refused).
3. `adhesion.clj` — for a façade-climbing (suction) robot: effective adhesion = nominal
   suction × a surface-type efficiency (glass best, porous stone worst); `adhesion-safe?`
   **RAISES** when the achieved factor-of-safety is below the required margin (**★ G7**).
4. `analyze.clj` — end-to-end R0 orchestrator: load `data/facade.edn` → coverage path +
   budget → wind/sway envelope → adhesion FoS → a top-level `:go?` = (wind permitted AND
   adhesion safe). A descent is planned only if BOTH gates pass.
5. `datom_emit.clj` — kotoba EAVT emitter (`:mado.face/* :mado.pane/* :mado.robot/*` +
   `:anchored-by` 縁 GROUND; `:bond/*` DERIVED transient).

**Privacy-by-construction (★ G3)** is structural: the cameras point AT the glass, but the data
model has **no** off-device / cloud / interior / person / biometric attribute — only
`:imagery {:on-device-only true :recognition :pane-edge-only}` and a single
`:mado.robot/imagery-on-device true` Datom are representable. Off-device imagery and interior
recognition are unrepresentable, and the test suite asserts both the model and the emitted
Datom log carry nothing else (mirrors kiyome on-device-no-cloud + manako no-biometric,
ADR-2606034800).

**Eight gates** (manifest `:actor/gates`): G1 design+sim-only/no-server-key · G2 water +
chemical minimization · **G3 privacy-by-construction (on-device imagery only)** · G4
Displacement-Dividend-coupled · **G5 wind work-stop + fall-arrest redundancy (raises)** · G6
Murakumo-only · **G7 adhesion factor-of-safety (raises)** · G8 tazuna-operated.

# Consequences

**Positive** — closes the highest-priority remote-work GAP (ADR-2606073001 §4 #1) with a
runnable R0 sim; the two fall-equivalent safety gates raise rather than soft-fail, so an
unsafe descent cannot be silently planned; privacy is structural (G3) not policy; reuses the
proven kuramori Clojure-first idiom (14 tests / 54 assertions green under `bb`);
Displacement-Dividend-coupled + tazuna-teleoperable by construction.

**Negative / limits** — R0 only: no hardware, no real actuation (G1); the sway model is
quasi-static single-point-suspension (no building-face guide rails, no dynamic gust spectrum —
R1); slotting of panes is one face at a time; the Clojure methods are not yet wired into the
langgraph cell runtime (cells are manifest scaffold; `.solve()` is R1).

**Follow-up (R1, gated)** — building-face guide-rail / restraint modelling + dynamic gust
response; multi-face / wrap-around buildings; cell-runtime wiring; on-device vision integration
with manako (ADR-2606034800) for pane-edge detection; the kuramori↔madomori façade-vs-floor
robotics handoff in the Datom log; live operation (operator/Council-gated).

# Alternatives Considered

- **Fold façade cleaning into kiyome 清め** — rejected: kiyome is indoor/ground-level with no
  fall-risk, rope/BMU, or wind-envelope concern; the façade hazard model is distinct.
- **Author in Python (canonical) and port later** — rejected per the Clojure-first GAP-wave
  decision (ADR-2606142000); madomori reuses the working kuramori idiom directly.
- **Treat safety thresholds as tunable parameters** — rejected: the wind work-stop and
  adhesion factor-of-safety are fall-equivalent gates; they raise and are not tunable up by a
  planner.

# References

- ADR-2606073001 (robotics remote-work actor roster + ISCO coverage/GAP survey — §4 ranks
  façade window cleaning the highest unmet remote-value GAP)
- ADR-2606142000 (kuramori 倉守 — reference Clojure-first actor idiom)
- ADR-2606032100 (labor-liberation OSS-robotics wave — sanae/hataori/kiyome)
- ADR-2606032130 (Displacement Dividend), ADR-2606042100 (tazuna 手綱 — teleop)
- ADR-2606034800 (manako 眼 — on-device browser-local vision; G3 on-device-no-cloud pattern)
- ADR-2605215000 (Murakumo-only), ADR-2605312345 (kotoba Datom = first-class canonical state)
