---
id: adr-2606142000-kuramori-warehouse-intralogistics-agv-amr
title: "ADR-2606142000: kuramori 倉守 — warehouse intralogistics robotics (AGV/AMR) + the Clojure-first GAP-actor wave"
status: accepted
doc_type: adr
topic: kuramori-warehouse-intralogistics
authoritative: true
last_verified: 2026-06-14
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Closes the warehouse-handling GAP named in ADR-2606073001 §3 (積み下ろし partial); first actor authored Clojure-first."
authoritative_for:
  - warehouse intralogistics robotics actor (AGV/AMR transport + slotting + putaway/picking)
  - the reference Clojure-first (babashka-runnable) actor idiom
depends_on:
  - ADR-2606082000 (niyaku — AGV/dispatch core reused)
  - ADR-2606073001 (robotics remote-work coverage/GAP survey — names kuramori as the warehouse GAP)
  - ADR-2606032130 (Displacement Dividend)
  - ADR-2606042100 (tazuna — teleop substrate)
  - ADR-2605215000 (Murakumo-only inference)
  - ADR-2605312345 (kotoba Datom = first-class canonical state)
related:
  - ADR-2606042300 (todoke — last-mile sibling)
  - ADR-2606032100 (labor-liberation robotics wave — sanae/hataori/kiyome)
supersedes: []
superseded_by: []
---

# ADR-2606142000: kuramori 倉守 — warehouse intralogistics robotics (AGV/AMR) + the Clojure-first GAP-actor wave

**Status**: accepted
**Date**: 2026-06-14
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

The robotics remote-work coverage survey (ADR-2606073001 §3) marked **積み下ろし
(loading/unloading)** as only *partial*: niyaku 荷役's 積込ロボット covers the port quay, and
todoke 届け covers the last mile, but **no actor covered the warehouse floor between them** —
the standalone intralogistics layer (AGV/AMR horizontal transport, slotting, putaway,
picking). The survey reserved the name `kuramori 倉守` for it.

This ADR authors kuramori, and in doing so opens the **Clojure-first GAP-actor wave**: the
in-flight Python→Clojure migration left 60 auto-port `.clj` stubs that are all non-functional
(`port-failed` TODOs) and untracked, so there was **no working Clojure actor anywhere in the
repo**. kuramori establishes the first one — methods authored directly in babashka-runnable
Clojure, pure (no deps) so they run under both `bb` and the kotoba pywasm runtime.

The warehouse transport mathematics is **not new** to the corpus: niyaku already proved the
trapezoidal/triangular travel-time profile, the one-way segment-conflict check, and greedy
LPT makespan dispatch in `agv_transfer.py` (ADR-2606082000). kuramori ports those exact
semantics rather than reinventing them.

# Decision

Author `20-actors/kuramori/` as a 🟡 R0 (design + sim) Tier-B actor.

**Reference Clojure-first idiom (reusable by the rest of the GAP wave):**
- methods are pure Clojure under `methods/<name>.clj` with ns `kuramori.methods.<name>`;
- tests are `methods/test_kuramori.clj` (`clojure.test`), self-exiting with a non-zero code
  on failure, run via `bb --classpath 20-actors <test-file>`;
- canonical state is projected to the kotoba EAVT Datom log via `datom_emit.clj` (GROUND
  `:add` durable; DERIVED `:derived` transient/computed-on-read — the asobi pattern).

**Methods:**
1. `agv_amr.clj` — AGV (fixed guidepath, segment reservations) vs AMR (free-roaming,
   shared-zone yield) motion; ports niyaku's trapezoidal travel-time + segment-conflict +
   LPT dispatch; **adds** a battery SoC + opportunity-charge gate (G2) and the
   collaborative-safety speed cap (G5).
2. `slotting.clj` — ABC velocity classing, golden-zone slotting, putaway feasibility
   (weight/temperature/hazmat — **raises** when infeasible, G7), nearest-neighbour pick-route.
3. `analyze.clj` — end-to-end R0 orchestrator (load → slot → pick-route → dispatch → battery).
4. `datom_emit.clj` — kotoba EAVT emitter (`:wh.zone/* :wh.slot/* :wh.sku/* :wh.robot/*` +
   `:slotted-in` 縁 GROUND; `:bond/*` DERIVED).

**Eight gates** (manifest `:actor/gates`): G1 design+sim-only/no-server-key · G2
zero-emission + charge gate · G3 no-worker-surveillance · G4 Displacement-Dividend-coupled ·
G5 shared-zone safety cap · G6 Murakumo-only · G7 hazmat-segregation-raises · G8
tazuna-operated.

# Consequences

**Positive** — closes the warehouse GAP (ADR-2606073001 §3) with a runnable R0 sim; proves
the first working Clojure-first actor idiom (15 tests / 43 assertions green under `bb`),
unblocking the rest of the GAP wave (soma / façade / sewer); reuses niyaku's proven transport
core instead of reinventing it; dividend-coupled + tazuna-teleoperable by construction.

**Negative / limits** — R0 only: no hardware, no real actuation (G1); slotting is one-SKU-
per-slot and dispatch is single-leg (no multi-pick consolidation or congestion replanning
yet — R1). The Clojure methods are not yet wired into the langgraph cell runtime (cells are
manifest scaffold; `.solve()` is R1).

**Follow-up (R1, gated)** — multi-pick order consolidation + congestion-aware replanning;
cell-runtime wiring; live WMS adapter (operator/Council-gated); the niyaku↔kuramori↔todoke
handoff edge (quay → warehouse → last-mile) in the Datom log.

# Alternatives Considered

- **Fold warehouse handling into niyaku** — rejected: niyaku is port-scoped (berth/STS/yard);
  the warehouse is a distinct facility with slotting/putaway/picking concerns niyaku lacks.
- **Author in Python (canonical) and port later** — rejected per the operator decision to go
  Clojure-first for the GAP wave; kuramori instead establishes the working Clojure idiom.
- **Reinvent the transport math** — rejected; niyaku's core is proven and tested.

# References

- ADR-2606073001 (robotics remote-work actor roster + ISCO coverage/GAP survey)
- ADR-2606082000 (niyaku 荷役 — port cargo handling; AGV/dispatch core)
- ADR-2606042300 (todoke 届け — last-mile), ADR-2606032130 (Displacement Dividend)
- ADR-2606042100 (tazuna 手綱 — teleop), ADR-2605215000 (Murakumo-only)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
