---
id: adr-2606091800-infra-robotics-3layer-operational-substrate
title: "ADR-2606091800: Basic-infrastructure robotics — 3-layer operational substrate (electric/water/gas/telecom)"
status: accepted
doc_type: adr
topic: infra-robotics-3layer-operational-substrate
authoritative: true
last_verified: 2026-06-09
priority: 5.0
axis: architecture
weight: 0.55
priority_note: ""
authoritative_for:
  - infra-robotics-operational-substrate
  - kuni-umi-robotics-reference-engine
depends_on: []
related:
  - "2605201400"
  - "2605261100"
  - "2605263100"
  - "2606051500"
  - "2606051600"
  - "2605215000"
  - "2605312345"
  - "2605231525"
supersedes: []
superseded_by: []
---

# ADR-2606091800: Basic-infrastructure robotics — 3-layer operational substrate (electric / water / gas / telecom)

**Status**: accepted
**Date**: 2026-06-09
**Deciders**: Jun Kawasaki

# Context

The basic-infrastructure actors (hikari 電気, mizuho 水道, kamado ガス/精製,
noroshi 通信/光配線) carried complete charter/ADR/cell **scaffolding** but almost
no runnable robotics: every domain `cell.py .solve()` raised `RuntimeError`, and
the only actor with real control code was noroshi (Hooke-Jeeves fibre alignment +
IEC 60825 gate). The field-tier control firmware **does** exist and is mature —
`60-apps/etzhayyim-project-open-ot/cells/` ships 8 IEC 61499 Rust WASM Function
Blocks (PID_LIMITED, DROOP_P_F, ANTI_ISLANDING_ROCOF, MPPT, LTC_TAP_FSM,
BLACK_START_SEQ, SOC_KALMAN) with cargo tests — but nothing connected those loops
to a plant model, to install-robot motion, or to kuni-umi's coordination /
witness layer. `kuni-umi/cells/commissioning/cell.py` literally raised
`NotImplementedError` at the `register_with_open_ot` / `commission_test` seam.

Separately, the reusable physics engine `40-engine/kami-engine` (kami-genesis
Featherstone solver, `giemon_arm6` fixture) is a **git submodule that is not
checked out** in working trees, so a Rust physics-sim path is not available
on-demand. We needed a way to make "the robot actually operates the
infrastructure" demonstrable and tested **now**, without weakening the
constitutional no-live-actuation gates.

# Decision

Introduce one shared **3-layer operational substrate** under
`20-actors/kuni-umi/robotics/` (the planetary-infra fleet coordinator owns the
reference engine; domain actors compose it) and replicate a single end-to-end
vertical pattern across all four basic-infra domains.

**The three layers**

1. **plant** (`plant.py`) — deterministic lumped-parameter plant simulation, the
   honest `:representative` **kami-genesis stand-in** until the submodule is
   checked out. `Plant` protocol + `FirstOrderPlant` + `MicrogridPlant`
   (swing-equation frequency + battery SoC). Domain actors add their own plants
   (reservoir, gas-concentration, cable-lay cross-track, fibre coupler).
2. **control** (`control.py`) — the floating-point **:representative twin of the
   open-ot field-tier WASM PLC**: `PID` (anti-windup), `Droop` (DROOP_P_F),
   `DroopPI` composite, and a `simulate()` closed-loop runner reporting
   convergence/settling. Hard-RT no-float servo stays in the open-ot Rust crates;
   this layer is the ≤10 Hz coordination + offline acceptance-test reference.
3. **kinematics** (`kinematics.py`) — install-robot motion: planar serial-arm FK +
   analytic 2-link IK + reachability + joint-space trajectory (what places a
   panel / reaches a cut point / aligns a fibre). The FK/IK contract is the
   subset the cells depend on, so swapping to the 6-DOF `giemon_arm6` solver when
   the submodule is present is mechanical.

Plus cross-cutting **`safety.py`**: closed-world civilian-use allowlist (N1,
weaponisation unrepresentable), no-server-key (`require_member_signature`,
G15/G7), witness quorum ≥2 (`witness_quorum_ok`, G8), and a motion
`SafetyEnvelope` whose joint-rate ceiling drops automatically when a person may
be in the work cell. And **`commissioning.py`**: the runnable kuni-umi → open-ot
handoff (microgrid acceptance test = droop-P-f load-step response + ROCOF
anti-islanding guard → dry-run loop-DID registration), which is now wired into
`CommissioningCell.commission_test` / `register_with_open_ot` (the live XRPC/MST
write still gated on `deps.sdk`).

**The per-domain pattern** (each actor): runnable control/motion loops in
`methods/` (importing the substrate via a `_substrate.py` sys.path shim), gated
phase transitions in `cells/<cell>/state_machine.py`, and `cell.py .solve()`
**unchanged — it still raises `RuntimeError` ("activate via Council ADR")**. The
runnable, tested code never actuates; it proves the loop converges and the gates
hold.

Domains delivered:

| Domain | Actor | Operational loop (runs + tested) | Key safety crux |
|---|---|---|---|
| 電気 | hikari | microgrid droop+PI restores 50 Hz after a load step; ROCOF guard; Otete-arm panel-install reach/IK/envelope | ROCOF trips on islanding-scale transient; slow joint ceiling near humans |
| 水道 | mizuho | reservoir PI level/pressure control; chlorination dosing | residual **hard-clamped** ≤ 4.0 mg/L (WHO/EPA); fluoride requires per-member consent (G6); G3 community-scale cap |
| ガス/精製 | kamado | PI purge drives H₂S/benzene below entry limit; arm IK to cut point | robot entry into an **un-purged** zone raises `SafetyError`; G3 decommission-only; G9 displacement cohort |
| 通信 | noroshi | fibre lay→align→splice (cable-lay path-tracking PI + existing Hooke-Jeeves aligner + fusion splice-loss model) | weapon laser use stays unenergisable (IEC 60825); splice rejected above 0.10 dB |

# Consequences

- **Positive.** "Basic-infrastructure robotics" moves from scaffold to a
  runnable, tested operational premise: **375 tests green** across the substrate
  (28) + electricity (25) + water (26) + gas (17 new) + telecom (41 new). The
  kuni-umi↔open-ot commissioning seam is no longer `NotImplementedError`. The
  three layers + safety/witness give every future infra actor a copy-paste
  template (noroshi/hikari are the worked examples).
- **Constitutional invariants preserved.** No live actuation: all `cell.py`
  `.solve()` entrypoints stay Council-gated; every record carries
  `server_held_key=False` + `dry_run=True`; the substrate is stdlib-only and
  touches no hardware/network. Murakumo-only inference is untouched (the loops are
  deterministic, no LLM). open-ot remains the hard-RT SSoT under a certified
  IEC 61508/61511 PLC — this substrate is its `:representative` offline twin, not
  a replacement.
- **Honest limits (`:representative`).** Plants are lumped-parameter models, not
  the kami-genesis Featherstone physics; gains are tuned for deterministic tests,
  not commissioning-grade. Activation to R1 (device-in-the-loop) still requires
  each actor's existing R1 trigger list (Council Lv6+, engineer on advisory,
  LANDS parcel, etc.) and the submodule-backed physics path.
- **Maintenance seam.** A method-module name that matches its cell-package name
  (mizuho `water_supply`, kamado `decommission_robot`) shadows on `sys.path`;
  resolved per-actor via `importlib`/path-append. Future actors should keep
  method-module names distinct from cell-dir names (as hikari does:
  `microgrid`/`grid_edge`).

# Alternatives Considered

- **Check out `40-engine/kami-engine` and build a Rust physics-sim path now.**
  Rejected for this R0: the submodule is heavy, the swap contract (FK/IK) is
  small, and a Python `:representative` layer is the documented G10 convention.
  The kinematics contract is written so the Rust swap is mechanical later.
- **Port the open-ot Rust BFBs to Python.** Unnecessary duplication — we mirror
  only the loop *behaviour* (PID/droop) needed for offline acceptance; the Rust
  crates stay the deployment SSoT.
- **Un-gate `cell.py .solve()` for a "real" feel.** Refused — it would breach the
  no-live-actuation / no-server-key invariants. The runnable surface lives in
  `methods/` + `state_machine.py`; `.solve()` stays gated (noroshi's pattern).

# References

- `20-actors/kuni-umi/robotics/` — substrate (plant / control / kinematics / safety / commissioning)
- `20-actors/{hikari,mizuho,kamado,noroshi}/methods/` + `/cells/` — the four verticals
- ADR-2605201400 — kuni-umi planetary-infra robotics fleet (coordination + witness invariant)
- `60-apps/etzhayyim-project-open-ot/` — IEC 61499 field-tier WASM PLC (the loops' Rust SSoT)
- ADR-2605261100 (hikari) · 2605263100 (mizuho) · 2606051500 (kamado) · 2606051600 (noroshi)
- ADR-2605215000 (Murakumo-only inference) · 2605312345 (kotoba Datom canonical state) · 2605231525 (no-server-key)
