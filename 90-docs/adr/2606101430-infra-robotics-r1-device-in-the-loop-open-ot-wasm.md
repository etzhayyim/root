---
id: adr-2606101430
title: "ADR-2606101430: Infra-robotics R1 device-in-the-loop — the REAL open-ot WASM cells close the microgrid loop"
status: accepted
doc_type: adr
topic: infra-robotics-r1-device-in-the-loop
authoritative: true
last_verified: 2026-06-10
priority: 5.0
axis: architecture
weight: 0.55
priority_note: "R1 of the 3-layer infra-robotics substrate: the deployment WASM artefacts (DROOP_P_F + ANTI_ISLANDING_ROCOF) replace the Python twin in the commissioning loop, per founder direction (Council gate exercised as PR merge, ibuki precedent)."
authoritative_for:
  - infra-robotics-r1-device-in-the-loop
  - device-loop-host line protocol
related:
  - adr-2606091800-infra-robotics-3layer-operational-substrate
  - adr-2606101130-session-close-infra-robotics-3layer-and-kami-physics-bridge
  - adr-2605201400 (kuni-umi planetary-infra fleet)
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606091800 (the 3-layer substrate this is R1 of)
---

# ADR-2606101430: Infra-robotics R1 device-in-the-loop — the REAL open-ot WASM cells close the microgrid loop

**Status**: accepted
**Date**: 2026-06-10
**Deciders**: Jun Kawasaki (founder direction 「device in the loop を進めてok」; Council gate exercised as PR merge, ibuki ADR-2606101200 precedent)

# Context

ADR-2606091800 shipped the 3-layer operational substrate with the control layer as a
**Python `:representative` twin** of the open-ot field tier, and listed
"open-ot acceptance-rig integration" as the gated follow-up: run the REAL Rust BFBs
under the wasmtime rig against the same plant scenarios the twin passes. Until now no
deployment artefact had ever closed a loop against a plant — gate-a-rig measures tick
latency on a fixed workload, it does not control anything.

# Decision

Promote the microgrid commissioning loop to **device-in-the-loop R1**: the device tier
is the actual deployment artefact — `droop_p_f.wasm` (2.8 KB) and
`anti_islanding_rocof.wasm` (4.3 KB), the open-ot IEC 61499 Rust BFBs compiled to
`wasm32-unknown-unknown` cdylib, the same artefact class WAMR executes on the Giemon
Cortex-M7 field hardware — executed under Wasmtime and driven tick-by-tick by the SAME
`MicrogridPlant` scenarios the Python twin passes.

**Pieces:**

1. **`device-loop-host`** (`60-apps/etzhayyim-project-open-ot/risk1/device-loop-host/`,
   Rust, wasmtime 36 — gate-a-rig's sibling): loads a BFB cell wasm, places
   Params/Internal/DataIn/DataOut at fixed high offsets (gate-a-rig memory map), and
   exposes a line protocol (`LOAD` / `INIT` / `TICK` / `QUIT`) on stdin/stdout so an
   external plant can close the loop. Knows nothing about plants or scenarios — it is
   the device tier only. Struct layouts come from the existing
   `codegen-cell-types.py` generated pack/unpack modules (the ABI contract).
2. **`device_loop.py`** (`20-actors/kuni-umi/robotics/`): spawns two hosts (droop +
   guard), runs three scenarios — normal +40 kW load step, load-shed, islanding-scale
   +90 kW step — with the real DROOP_P_F computing the primary droop term (+ the same
   Python secondary-PI trim the twin uses) and the real ANTI_ISLANDING_ROCOF watching
   the frequency stream. Writes the committed golden
   `golden/device_loop_trace.json`, so verification runs without cargo/wasmtime.
3. **Commissioning R1 tier**: `commission_microgrid_site(..., device_evidence=...)` —
   consistent device evidence upgrades the record's `acceptance_tier` from
   `"python-twin"` to `"device-wasm"`; inconsistent evidence demotes the site to
   punch-list (**evidence can only tighten, never loosen**). The CommissioningCell's
   `commission_test` node reads the committed golden the same way.

**Two semantic findings the loop surfaced (now load-bearing, test-pinned):**

- **DROOP_P_F is incremental**: `p_setpoint = clamp(current_p + Δ(f))`. Feeding the
  last total command back as `current_p` turns the cell into an integrator (observed:
  >180 kW divergence from the twin). Correct usage feeds the FIXED dispatch base, making
  it the absolute droop-around-dispatch the twin computes.
- **Unit conventions differ**: the device implements per-unit droop
  (Δp = Δf/(f_nom·R)·P_rated); the Python `Droop` is absolute (Δp = Δf/R). The exact
  equivalence map is `R_twin = f_nom·R_dev/P_rated` — derived in code, not tuned.

**Result (committed golden):** all three scenarios — frequency restored to 50.0 Hz on
normal/load-shed with no trip; the REAL guard **latches a trip** on the islanding-scale
step; per-step command parity with the Python twin = **0.0001 kW** (exactly the µkW
integer quantisation); device verdicts match the twin verdicts on every scenario.

Also fixed in passing: `validate-cell-abi.py` ALLOWED_WIRE had drifted behind the
later-wave cells (soc-kalman `valueMilliUnit`, black-start/ltc-tap/mppt enum + duration
wires) — its `test_real_repo_content_passes` was red on main; now green (26 tests).

# Consequences

- The "device" in device-in-the-loop is the byte-for-byte deployment artefact, so
  commissioning evidence now speaks for the field tier, not a lookalike. The
  twin-equivalence map makes the Python twin a *calibrated* stand-in rather than an
  approximate one.
- Tests: kuni-umi/robotics 36 → **48** (9 device-loop incl. 2 live e2e that execute the
  wasm when the host is built, golden-only otherwise; 3 commissioning-tier) + open-ot
  validator suite back to green (26) + codegen (14). Full sweep across the four
  verticals unchanged.
- Invariants unchanged: offline sim + dry-run evidence only; every record
  `server_held_key=False` + `dry_run=True`; the host holds no key and signs nothing;
  live dispatch to field hardware stays Council/operator-gated behind `deps.sdk` + the
  certified IEC 61508/61511 safety PLC. Hard-RT stays in the field tier.
- Honest limits: Wasmtime on a Mac is not WAMR-AOT on a Cortex-M7 (timing differs;
  logic/ABI identical); voltage is held nominal in these scenarios (the guard's
  voltage/freq windows are exercised wide); BLACK_START_SEQ and the remaining 6 BFBs
  are not yet in the loop.

# Alternatives Considered

- **wasmtime-py driver** — rejected: adds a pip dependency to an actor tree that is
  deliberately stdlib-only; the Rust host reuses the proven gate-a-rig embedding and
  keeps Python pure.
- **Re-implementing the plant in Rust inside the rig** — rejected: the whole point is
  that the SAME plant code that accepted the twin accepts the device.
- **Waiting for physical hardware** — rejected: executing the deployment artefact under
  a host runtime is the standard pre-hardware HIL stage and is what the follow-up
  specified.

# References

- `60-apps/etzhayyim-project-open-ot/risk1/device-loop-host/` — the device host
- `20-actors/kuni-umi/robotics/{device_loop.py, test_device_loop.py, golden/device_loop_trace.json}`
- `20-actors/kuni-umi/robotics/commissioning.py` (`acceptance_tier`) + `cells/commissioning/cell.py`
- ADR-2606091800 · ADR-2606101130 · ADR-2606101200 (Council-gate-as-PR-merge precedent)
