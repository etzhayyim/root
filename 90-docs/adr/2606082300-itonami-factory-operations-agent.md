---
id: adr-2606082300-itonami-factory-operations-agent
title: "ADR-2606082300: itonami 営み — factory-operations agent (charter-clean FOX inversion)"
status: accepted
doc_type: adr
topic: itonami-factory-operations-agent
authoritative: true
last_verified: 2026-06-08
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes the 'run the factory' gap (FOX/AI-Factory-Brain operational layer) left open by the build-side factory sims (giemon/sarutahiko/tatekata)."
authoritative_for:
  - itonami 営み actor (factory-operations agent)
  - itonami-ontology
depends_on:
  - 2606031600
  - 2606013100
  - 2606034800
  - 2605311800
  - 2605312345
  - 2605215000
  - 2605241500
related:
  - 2606010030
  - 2605250715
  - 2606014500
  - 2605261600
supersedes: []
superseded_by: []
---

# ADR-2606082300: itonami 営み — factory-operations agent (charter-clean FOX inversion)

**Status**: accepted
**Date**: 2026-06-08
**Deciders**: Jun Kawasaki

# Context

The monorepo's manufacturing capability is strong on the **"build the factory"** side —
giemon-factory (ADR-2606010030) and sarutahiko truck line (ADR-2606013100) run 4D-BIM
construction + production-line sims on real kami-genesis physics (ADR-2605311800), and
kotoba-os (ADR-2606031600) models PLC control as **scan-cycle = Datom transaction**.

It is empty on the **"run the factory"** side. A survey against NVIDIA's *Factory Operations
Blueprint (FOX)* / Advantech "AI Factory Brain" (the platform that wires AI agents into a
*running* plant for energy / quality / throughput optimization, reported 2026-06) found **no
actor** covering: (1) energy-optimization, (2) vision-inspection in production, (3) SCADA/OT
operating-data → optimization loop, (4) a factory-operations agent platform. hikari (energy)
and manako (vision) exist as bodies but nothing fuses operating data into operational
intelligence.

FOX is also a clean illustration of *why* a naive port would violate the Charter: floor
monitoring slides into worker surveillance, and "optimize throughput" slides into labor
intensification — both Wellbecoming (§1.13) violations — and write-back to the OT bus
violates the no-server-key / no-live-actuation invariants.

# Decision

Introduce **itonami 営み** (the *running/operation* of an enterprise), a Tier-B
factory-operations agent that is the **charter-clean inversion of FOX**. It performs the same
operational maths and inverts the telos and the boundary:

1. **Observe → recommend only (G1).** itonami ingests scan-cycle observations (the kotoba-os
   scan-cycle Datom analog) and computes per-station + line KPIs, then *routes* findings to a
   human / Council. It **never** writes back to the OT bus (no-server-key, liveActuation:false).
2. **Station/line scale only (G2).** There is no `:worker/*`/`:person/*` namespace; per-person
   productivity / pace / presence is **structurally unrepresentable** (anti-labor-surveillance,
   Wellbecoming §1.13). Gains route to *efficiency*, never to line-speed-up / intensification.
3. **kotoba-native, non-adjudicating (G3).** Scan-cycle ticks are durable EAVT ground datoms
   (canonical state, ADR-2605312345); KPIs are read-time aggregates flagged
   `:bond/is-transient`, never durable verdicts.

## KPIs (R0)

Canonical manufacturing metrics, aggregate-first:

- **OEE = Availability × Performance × Quality** per station; line OEE = the weakest station
  (a serial line *is* its bottleneck).
- **energy/good-unit (kWh)** + **idle-energy fraction** (energy burned while not producing) —
  the FOX "cut 10% energy" lever, expressed as efficiency, not speed-up.
- **scrap-rate** — routed to vision inspection (**manako**, ADR-2606034800) + root-cause.

Routed findings: `bottleneck`, `energy_target`, `idle_energy_target`, `quality_target`.

## Placement

The **observer** paired with the build-side sims:

```
build:  giemon-factory / sarutahiko line / tatekata   (kami-genesis physics)
run OT: kotoba-os scan-cycle Datoms (ADR-2606031600)
  →     itonami OEE / energy / quality  ──┬─► manako (vision, quality)
                                          ├─► hikari (energy)
                                          └─► toritate (ledger)
```

The R0 seed is the sarutahiko 8-cell line, binding the observer to an existing build sim.

# Gates

- **G1** observe→recommend, never actuate (no write-back to the OT bus).
- **G2** station/line scale only; no worker/person dimension (anti-labor-surveillance).
- **G3** non-adjudicating; KPIs transient, ticks durable.
- **G4** civilian producing actors only (Charter §1.12).
- **G5** sourcing honesty; R0 seed is `:representative` synthetic, never live OT.
- **G6** outward-gated; live OT/SCADA ingest (Modbus/OPC-UA/EtherCAT via kotoba-os device
  worlds) requires Council + operator DID.
- **G7** Murakumo-only narration (ADR-2605215000).

# Consequences

**Positive**: closes the operational ("run the factory") gap with a charter-clean inversion
that is *structurally* incapable of worker surveillance or line actuation; reuses existing
substrate (kotoba Datom log, kotoba-os scan-cycle, sarutahiko line); pure-stdlib pywasm-ready.

**Negative / limits**: R0–R11 are computed from a `:representative` synthetic seed, not live OT
(live scan-cycle socket is G6/Council-gated; `ingest.py` does offline Datom replay only). KPIs
are aggregates of disclosed counts, not a physics-faithful plant model. The vision hand-off
emits a manako inspection request + reconciles a detection log, but does not run the detector.
No componentize-py `.wasm` is built yet (R12); the actor entrypoint is verified via the CLI/test
path. The OEE↔sarutahiko-produce-sim cross-check remains future (R12).

# Roadmap

R0–R11 landed in one session (9 cells + the WASM actor entrypoint; **87 tests green**,
pure-stdlib pywasm-ready). Per-cell detail lives in `20-actors/itonami/CLAUDE.md`.

- **R0 ✅** — `analyze.py` (OEE=A×P×Q / energy / quality, routed findings) + `datom_emit.py`
  (canonical EAVT) + `itonami-ontology.kotoba.edn` + sarutahiko 8-cell seed. 10 tests.
- **R1 ✅** — `optimize.py`: idle-power-down energy-reduction proposal (honest %, not inflated to
  FOX's 10%) + bottleneck-relief. 6 tests.
- **R2 ✅** — `inspect.py`: manako 眼 (ADR-2606034800) vision-inspection hand-off + defect-Pareto
  reconcile; object-only, never a person (G2). 7 tests.
- **R3 ✅** — `ingest.py`: SCADA/OT scan-cycle Datom-stream fold → ticks (offline replay; live
  socket G6-gated). 10 tests.
- **R4 ✅** — `digest.py`: fused daily digest + Murakumo-only narration (G7), deterministic
  offline fallback. **R6 ✅** folds in the throughput two-lens, **R8 ✅** folds in multi-day drift.
  13 tests.
- **R5 ✅** — `plan.py`: throughput / line-balance via the takt-capacity lens (throughput-worst ≠
  OEE-worst); units/day + availability-recovery relief. 8 tests.
- **R7 ✅** — `trend.py`: KPI drift detector over durable daily `:opsday/*` snapshots (as-of
  trajectory; polarity-aware direction). 8 tests.
- **R9 ✅** — `alert.py`: graded threshold alerts (HMI alarm half), ADVISORY ONLY — never halts /
  trips / writes to the OT bus (no actuation token representable). 9 tests.
- **R10 ✅** — `fleet.py`: multi-line plant rollup + attention ranking (ranks LINES, never
  people). 7 tests.
- **R11 ✅** — `actor.py`: pywasm actor entrypoint wiring the nine cells into one WIT-sketched
  export surface (summary/analyze/digest/alert/fleet JSON + datoms EDN); READ-ONLY by
  construction. 9 tests.
- **R12 (next)** — componentize-py WASM build + content-addressed `did.json` service wiring;
  live scan-cycle socket (Council + operator DID gated); cross-check OEE vs the sarutahiko
  produce sim (kami-engine).

# Alternatives considered

- **Extend kotoba-os** to compute KPIs in-kernel — rejected; kotoba-os is the *control*
  substrate (scan-cycle execution), itonami is the *observation/intelligence* layer. Keeping
  them separate preserves the no-actuation boundary (itonami literally has no OT write path).
- **Extend sarutahiko** with an ops dashboard — rejected; operations intelligence is
  cross-actor (giemon/tatekata/mitsuho lines too), so it warrants its own actor.
