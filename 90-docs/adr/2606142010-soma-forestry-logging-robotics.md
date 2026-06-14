---
id: adr-2606142010-soma-forestry-logging-robotics
title: "ADR-2606142010: soma 杣 — forestry / logging robotics (directional felling + bucking + extraction)"
status: accepted
doc_type: adr
topic: soma-forestry-logging-robotics
authoritative: true
last_verified: 2026-06-14
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Closes the 伐採 (logging) GAP the robotics remote-work survey reserved (ADR-2606073001 §4, 'one of the deadliest jobs'); second actor in the Clojure-first GAP-actor wave (mirrors kuramori ADR-2606142000)."
authoritative_for:
  - forestry / logging robotics actor (directional felling + cut-to-length bucking + slope/soil-limited extraction)
depends_on:
  - ADR-2606073001 (robotics remote-work survey — §4 reserves soma 杣 for 伐採)
  - ADR-2606032100 (labor-liberation OSS-robotics wave — sanae/hataori/kiyome pattern)
  - ADR-2606032130 (Displacement Dividend)
  - ADR-2606042100 (tazuna — teleop substrate)
  - ADR-2605215000 (Murakumo-only inference)
  - ADR-2605312345 (kotoba Datom = first-class canonical state)
related:
  - ADR-2606142000 (kuramori 倉守 — the Clojure-first reference actor soma mirrors)
supersedes: []
superseded_by: []
---

# ADR-2606142010: soma 杣 — forestry / logging robotics (directional felling + bucking + extraction)

**Status**: accepted
**Date**: 2026-06-14
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

The robotics remote-work coverage survey (ADR-2606073001 §4) reserved the name `soma 杣` for
**伐採 (logging/felling)** and flagged it as one of the deadliest civilian occupations — fall
fatalities, struck-by, and machines sliding on steep wet terrain. The roster had a logging
GAP: nothing covered cutting, bucking, and extracting timber. soma fills it.

soma extends the **Clojure-first GAP-actor wave** opened by kuramori 倉守 (ADR-2606142000): the
in-flight Python→Clojure migration left non-functional auto-port stubs, so kuramori established
the first working Clojure-first actor idiom. soma is the second, mirroring that idiom exactly —
pure Clojure methods (no deps) that run under both `bb` (babashka) and the kotoba pywasm runtime.

The actor's raison d'être is **taking the human out of the fall zone** while remaining
ecologically disciplined: it is selective + regenerative only, it never clear-cuts, and it
never fells protected/old-growth trees. The two safety classes that make logging lethal —
unpredictable fall direction and unstable extraction terrain — are encoded as structural
refusals, not advisories.

# Decision

Author `20-actors/soma/` as a 🟡 R0 (design + sim) Tier-B actor, following the kuramori
Clojure-first idiom (methods under `methods/<name>.clj`, ns `soma.methods.<name>`; tests in
`methods/test_soma.clj` self-exiting non-zero on failure; canonical state projected to the
kotoba EAVT Datom log via `datom_emit.clj`, GROUND `:add` durable + DERIVED `:derived` transient).

**Methods:**
1. `fell_plan.clj` — directional tree-felling mechanics. Predicts the fall azimuth from the
   notch/hinge cut aim, biased by the tree's natural lean and perturbed by wind; computes the
   hinge holding-wood width (≈10% of DBH). The fall zone is a ≈1.5×-tree-height sector around
   the fall line. `safe-fell?` is false and `plan-fell` **RAISES** when that zone overlaps any
   exclusion (human/road/watercourse, **G5**) or when the tree is protected/no-cut (**G7**).
2. `harvester.clj` — cut-to-length bucking value optimization (an unbounded rod-cutting DP over
   a price-by-length-class table, sawlog > pulp) + a grapple/boom reach feasibility check (G8).
3. `extraction.clj` — forwarder/skidder extraction. A slope gate refuses any segment over the
   machine's max grade; a ground-impact gate refuses operating over the soil's bearing limit or
   on protected soil. `plan-route` **RAISES** on either (**G2** regenerative-only).
4. `analyze.clj` — end-to-end R0 orchestrator: load seed → per-tree fell (aim into a clear lane,
   refuse protected/unsafe trees) → buck → extraction route → report map.
5. `datom_emit.clj` — kotoba EAVT emitter (`:soma.stand/* :soma.tree/* :soma.exclusion/*
   :soma.forwarder/*` + `:felled` / `:refused-protected` 縁 GROUND; `:bond/*` DERIVED transient).

**Eight gates** (manifest `:actor/gates`): G1 design+sim-only/no-server-key · G2
selective+regenerative (clear-cut unrepresentable; extraction slope/soil raises) · G3
no-worker-surveillance · G4 Displacement-Dividend-coupled · **G5 exclusion-zone fell safety
(raises)** · G6 Murakumo-only · **G7 protected-species/no-cut refusal (raises)** · G8
tazuna-operated (weaponizable use unrepresentable).

# Consequences

**Positive** — closes the 伐採 GAP (ADR-2606073001 §4) with a runnable R0 sim; the two
fatality classes are structural refusals (G5 fall-zone, G2 slope/soil) rather than overridable
warnings; second working Clojure-first actor (16 tests / 67 assertions green under `bb`),
confirming the kuramori idiom generalises; dividend-coupled + tazuna-teleoperable by construction.

**Negative / limits** — R0 only: no hardware, no real actuation (G1); the fall-direction model
is a planning-grade geometric approximation (lean + wind vector resolution, not a full dynamic
tree-fall simulation); bucking is single-stem (no whole-tree value chain optimization yet); the
Clojure methods are not yet wired into the langgraph cell runtime (cells are manifest scaffold;
`.solve()` is R1).

**Follow-up (R1, gated)** — higher-fidelity fall dynamics (barber-chair / hang-up detection);
whole-stand harvest scheduling + skid-trail network optimization; cell-runtime wiring; live
machine adapter (operator/Council-gated); the soma → kuramori → todoke handoff edge (forest
landing → warehouse → last-mile) in the Datom log.

# Alternatives Considered

- **Fold logging into sanae 早苗 (agriculture robotics)** — rejected: agriculture and forestry
  share a regenerative ethos but the mechanics (directional felling, bucking, steep-terrain
  extraction) and the fatality profile are distinct enough to warrant a dedicated body.
- **Author in Python (canonical) and port later** — rejected per the operator decision to go
  Clojure-first for the GAP wave; soma mirrors the kuramori working Clojure idiom.
- **Treat the fall-zone check as a warning** — rejected: fall fatality is the #1 logging hazard;
  G5 must be a refusal (`plan-fell` raises), not an overridable advisory.

# References

- ADR-2606073001 (robotics remote-work actor roster + ISCO coverage/GAP survey — §4 reserves soma)
- ADR-2606142000 (kuramori 倉守 — Clojure-first reference actor)
- ADR-2606032100 (labor-liberation OSS-robotics wave), ADR-2606032130 (Displacement Dividend)
- ADR-2606042100 (tazuna 手綱 — teleop), ADR-2605215000 (Murakumo-only)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
