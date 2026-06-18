---
id: adr-2606142030-kudamori-sewer-confined-space-cleaning-robotics
title: "ADR-2606142030: kudamori 管守 — sewer / confined-space in-pipe cleaning robotics"
status: accepted
doc_type: adr
topic: kudamori-sewer-confined-space-cleaning
authoritative: true
last_verified: 2026-06-14
priority: 5.0
axis: architecture
weight: 0.50
priority_note: "Closes the toxic-gas/confined-space-death GAP named in ADR-2606073001 §4; in-pipe cleaning counterpart that mizuho 水穂 (treatment) left open. Clojure-first GAP-actor wave (sibling of kuramori)."
authoritative_for:
  - sewer / confined-space in-pipe cleaning robotics actor (atmosphere gate + nav + jetting)
depends_on:
  - ADR-2606073001 (robotics remote-work survey — §4 names confined-space death as a high-remote-value GAP)
  - ADR-2606032100 (labor-liberation OSS-robotics wave)
  - ADR-2606032130 (Displacement Dividend)
  - ADR-2606042100 (tazuna — teleop substrate)
  - ADR-2605215000 (Murakumo-only inference)
  - ADR-2605312345 (kotoba Datom = first-class canonical state)
related:
  - ADR-2606142000 (kuramori — Clojure-first reference actor / sibling)
  - ADR-2605263100 (mizuho 水穂 — water + sanitation; treatment counterpart, effluent handoff)
supersedes: []
superseded_by: []
---

# ADR-2606142030: kudamori 管守 — sewer / confined-space in-pipe cleaning robotics

**Status**: accepted
**Date**: 2026-06-14
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

The robotics remote-work coverage survey (ADR-2606073001 §4) flagged **toxic-gas /
confined-space death** as a high-remote-value robotics GAP: sending a worker down a manhole
into an oxygen-deficient, H2S-laden, methane-prone sewer to clean a blockage is among the
deadliest jobs that a robot should be doing instead. The roster already has mizuho 水穂
(ADR-2605263100), but mizuho covers wastewater *treatment* — community-scale process plant —
**not the in-pipe cleaning** that actually puts a human in the confined space. That cleaning
leg was an open GAP.

This ADR authors **kudamori 管守** ("pipe-keeper") to close it: an electric, tazuna-teleoperable
in-pipe crawler that **removes the human from the confined space**. It joins the Clojure-first
GAP-actor wave opened by kuramori (ADR-2606142000) — methods authored directly in
babashka-runnable Clojure, pure (no deps) so they run under both `bb` and the kotoba pywasm
runtime.

# Decision

Author `20-actors/kudamori/` as a 🟡 R0 (design + sim) Tier-B actor, mirroring the
kuramori Clojure-first idiom (pure `methods/<name>.clj`, ns `kudamori.methods.<name>`,
self-exiting `clojure.test`, kotoba EAVT `datom_emit`).

**Methods:**
1. `atmosphere.clj` (★ **G5**) — the confined-space ENTRY GATE: `entry-permitted?` /
   `assert-entry!` check O2 (19.5–23.5 %), H2S (<10 ppm), CH4 (<10 %LEL), CO (<35 ppm); an
   unsafe reading **RAISES** — entry without a passing atmosphere is unrepresentable. A
   `purge-to-entry` forced-ventilation model relaxes contaminants toward 0 and O2 toward
   fresh-air 20.9 %, and admits entry **only** when the post-purge reading actually passes
   (it never lies about safety). Mirrors niyaku/kamado purge-to-entry discipline.
2. `pipe_nav.clj` — in-pipe crawler navigation: a diameter-fit check (`assert-fit!` RAISES
   when crawler OD + clearance exceeds pipe ID), BFS shortest route over the (undirected)
   pipe-network graph, and route-around of blocked segments (or flag-the-blockage when it is
   the cleaning target).
3. `jetting.clj` (★ **G7**) — hydro-jetting: `jet-pressure-safe?` / `assert-jet-pressure!`
   compare nozzle pressure to the pipe material's working rating (VCP/PVC/concrete/
   ductile-iron); over-pressure **RAISES** (never clamp-and-proceed). Plus a debris-removal
   volume estimate and a water-reuse balance whose residual effluent is handed to mizuho
   (G2 — never discharged untreated).
4. `analyze.clj` — end-to-end R0 orchestrator: entry gate (purge if needed) → in-pipe nav →
   pressure-safe jetting → report; downstream legs report `:gated` when the atmosphere cannot
   be made safe.
5. `datom_emit.clj` — kotoba EAVT emitter (`:kuda.node/* :kuda.pipe/* :kuda.robot/*` +
   `:cleans` 縁 GROUND `:add`; `:bond/*` DERIVED `:derived` transient — the asobi pattern).

**Eight gates** (manifest `:actor/gates`): G1 design+sim-only/no-server-key · G2
water-reuse/eco + effluent→mizuho · G3 no-worker-surveillance · G4
Displacement-Dividend-coupled · ★ G5 confined-space-atmosphere-gate-raises · G6 Murakumo-only
· ★ G7 no-pipe-over-pressure-raises · G8 tazuna-operated.

# Consequences

**Positive** — closes the confined-space-death GAP (ADR-2606073001 §4) with a runnable R0
sim; makes the two unsafe acts (unsafe entry, over-pressure jetting) **unrepresentable** as
raising asserts proven by tests; reuses the Clojure-first idiom established by kuramori (17
tests / 55 assertions green under `bb`); dividend-coupled + tazuna-teleoperable by
construction; cleanly seams to mizuho for effluent treatment.

**Negative / limits** — R0 only: no hardware, no real actuation (G1). The atmosphere model is
a well-mixed single-zone dilution (no stratification / hot-spots); navigation is hop-count
BFS (no hydraulic/flow cost); jetting pressure ratings are conservative R0 placeholders, not a
material-spec database. The Clojure methods are not yet wired into the langgraph cell runtime
(cells are manifest scaffold; `.solve()` is R1).

**Follow-up (R1, gated)** — continuous gas-monitoring during the run (re-gate on a rising
reading, not just at entry); flow/hydraulic-cost routing + CCTV inspection pass; a real
pipe-material pressure-rating table; cell-runtime wiring; the mizuho effluent-handoff edge in
the Datom log; live operation operator/Council-gated.

# Alternatives Considered

- **Fold in-pipe cleaning into mizuho 水穂** — rejected: mizuho is treatment-plant-scoped
  (process units, chlorination, consent gates); the in-pipe crawler is a distinct mobile body
  with atmosphere/navigation/jetting concerns mizuho lacks. They seam (effluent handoff) but
  are separate actors.
- **Author in Python (canonical) and port later** — rejected per the operator decision to go
  Clojure-first for the GAP wave; kudamori follows the working kuramori idiom.
- **Treat the atmosphere gate as a warning, not a raise** — rejected: the entire value of the
  actor is removing the human from a lethal space, so unsafe entry must be unrepresentable,
  not merely flagged (★ G5).

# References

- ADR-2606073001 (robotics remote-work actor roster + ISCO coverage/GAP survey — §4)
- ADR-2606142000 (kuramori 倉守 — Clojure-first reference actor / sibling)
- ADR-2605263100 (mizuho 水穂 — water + sanitation; treatment counterpart)
- ADR-2606032100 (labor-liberation OSS-robotics wave), ADR-2606032130 (Displacement Dividend)
- ADR-2606042100 (tazuna 手綱 — teleop), ADR-2605215000 (Murakumo-only)
- ADR-2605312345 (kotoba Datom = first-class canonical state)
