---
id: adr-2606101845
title: "ADR-2606101845: Session-Close — infra-robotics R1 device-in-the-loop wave (real open-ot WASM in the commissioning loop)"
status: accepted
doc_type: adr
topic: session-close-infra-robotics-r1-device-in-the-loop
authoritative: true
last_verified: 2026-06-10
priority: 5.0
axis: process
weight: 0.50
priority_note: "Session-close record for the wave that executed ADR-2606091800 follow-up #3: the real open-ot deployment artefacts (DROOP_P_F + ANTI_ISLANDING_ROCOF wasm) close the microgrid commissioning loop under Wasmtime, with twin parity at integer-quantisation level."
authoritative_for:
  - session-close summary of the R1 device-in-the-loop wave (2026-06-10)
  - deps.toml registration of ADR-2606101430
related:
  - adr-2606101430-infra-robotics-r1-device-in-the-loop-open-ot-wasm
  - adr-2606091800-infra-robotics-3layer-operational-substrate
  - adr-2606101130-session-close-infra-robotics-3layer-and-kami-physics-bridge
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606101430 (the substance of this session)
---

# ADR-2606101845: Session-Close — infra-robotics R1 device-in-the-loop wave

**Date**: 2026-06-10
**Status**: ACCEPTED (process record)
**Deciders**: Jun Kawasaki

# Context

Continuation of the infra-robotics line (ADR-2606091800 3-layer substrate, PR #1531
merged; ADR-2606101130 kami-physics bridge, PR #1538 merged). The founder directed
*「device in the loop を進めてok」* — authorising the gated follow-up #3 (open-ot
acceptance-rig integration) under the Council-gate-as-PR-merge convention
(ibuki ADR-2606101200 precedent). Per-actor R1 hardware triggers (domain engineer on
advisory, LANDS parcel, etc.) remain open; this wave is the pre-hardware HIL stage:
the deployment artefact itself, not a lookalike, in the loop.

# What was done (PR #1568 → ADR-2606101430)

1. **`device-loop-host`** — new Rust binary in `60-apps/etzhayyim-project-open-ot/risk1/`
   (workspace member, gate-a-rig's sibling, wasmtime 36): loads a BFB cell wasm,
   places Params/Internal/DataIn/DataOut at the gate-a memory-map offsets, exposes a
   `LOAD`/`INIT`/`TICK`/`QUIT` line protocol on stdin/stdout. The device tier only —
   knows nothing about plants or scenarios.
2. **`device_loop.py`** + committed golden (`20-actors/kuni-umi/robotics/`): the real
   `droop_p_f.wasm` (2.8 KB) + `anti_islanding_rocof.wasm` (4.3 KB), built
   wasm32-unknown-unknown from the open-ot cells, close the loop against the same
   `MicrogridPlant` scenarios the Python twin passes. Golden result: 50.0 Hz restored
   on normal/load-shed (no trip), the REAL guard latches on the islanding-scale step,
   per-step twin parity **0.0001 kW** (exactly the µkW integer quantisation), verdict
   match on every scenario.
3. **Two real-cell semantics surfaced and test-pinned**: DROOP_P_F is incremental
   (feed the FIXED dispatch base — feeding the last command back integrates, observed
   >180 kW divergence) and the per-unit vs absolute droop unit-equivalence
   `R_twin = f_nom·R_dev/P_rated` (derived, not tuned).
4. **Commissioning R1 tier**: `acceptance_tier` `"python-twin"` → `"device-wasm"` on
   consistent device evidence; inconsistent evidence demotes the site to punch-list
   (evidence only tightens). The CommissioningCell `commission_test` node reads the
   committed golden.
5. **Fixed in passing**: `validate-cell-abi.py` `ALLOWED_WIRE` drift — the open-ot ABI
   gate's `test_real_repo_content_passes` was red on main (soc-kalman / black-start /
   ltc-tap / mppt wires); now green (26 tests).
6. **Registrations (this ADR's wave)**: deps.toml `[[adrs]]` 2606101430 + this
   session-close; `[[modules]]` kuni-umi/robotics status → R0+R1; CLAUDE.md status row
   → R0+R1 / 395 tests; registries regenerated.

# Consequences

- Commissioning evidence now speaks for the field tier byte-for-byte; the Python twin
  is a *calibrated* stand-in (exact equivalence map) rather than an approximate one.
- Tests: kuni-umi/robotics 36 → 48 (2 live e2e execute the wasm when the host is
  built; golden-only otherwise) · full vertical sweep 395 · open-ot validator 26.
- Invariants unchanged: offline dry-run evidence only; `server_held_key=False` +
  `dry_run=True` on every record; the host signs nothing; live field dispatch stays
  Council/operator-gated behind `deps.sdk` + the certified IEC 61508/61511 PLC.
- Honest limits: Wasmtime-on-Mac ≠ WAMR-AOT-on-Cortex-M7 (timing differs; logic/ABI
  identical); voltage held nominal in the scenarios; BLACK_START_SEQ + the 6 remaining
  BFBs not yet in the loop.

# Follow-ups (tracked, gated)

1. **Remaining BFBs into the loop** — BLACK_START_SEQ (black-start acceptance leg),
   SOC_KALMAN (battery SoC evidence), VV_CURVE/LTC/MPPT as their plant models land.
2. **WAMR-AOT timing leg** — re-run the golden scenarios under wamrc-compiled AOT on
   target-class hardware when available (the timing half of the device claim).
3. **Per-actor R1 hardware triggers** — unchanged (Council advisory engineer, LANDS
   parcel, sourcing audits) before any live field dispatch.

# References

- ADR-2606101430 — the substance · PR #1568
- `60-apps/etzhayyim-project-open-ot/risk1/device-loop-host/` ·
  `20-actors/kuni-umi/robotics/{device_loop.py,golden/device_loop_trace.json}`
- ADR-2606091800 · ADR-2606101130 · ADR-2606101200 (gate-as-PR-merge precedent)
