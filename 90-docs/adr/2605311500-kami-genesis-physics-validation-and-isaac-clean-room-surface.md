---
id: adr-2605311500-kami-genesis-physics-validation-and-isaac-clean-room-surface
title: "ADR-2605311500: kami-genesis physics maturation — PlanarChain articulation, clean-room isaacsim.core.api surface, analytical/conservation-law validation, and G5 Isaac-reference scorecard"
status: accepted
doc_type: adr
topic: kami-genesis-physics-validation
authoritative: true
last_verified: 2026-05-31
priority: 5.5
axis: architecture
weight: 0.5
priority_note: "Session record for the physics-engine maturation loop: generalizes kami-genesis from cartpole + 2-link to N-link planar reduced-coordinate arms, adds a clean-room isaacsim.core.api surface (no NVIDIA linkage), and establishes the 'how do we know it is correct' answer the user asked for — analytical/closed-form + conservation-law tests now, plus a drop-in Isaac-reference-CSV G5 scorecard for later offline cross-check. All claims verified by direct cargo-test observation."
authoritative_for:
  - kami-genesis PlanarChain (N≥3 serial revolute) articulation topology
  - kami-genesis clean-room isaacsim.core.api World/Articulation surface scope
  - physics-correctness validation strategy (analytical + conservation law + G5 reference CSV)
  - G5 reference-CSV scorecard harness contract and Isaac-CSV drop-in path
depends_on:
  - adr-2605261800-nvidia-omniverse-stack-api-compat
  - adr-2605261600-robotics-simulation-substrate-r0
  - adr-2605272000-isekai-omniverse-r1-1-usd-physx-playable
related:
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
supersedes: []
superseded_by: []
---

# ADR-2605311500: kami-genesis physics maturation — PlanarChain, clean-room Isaac surface, validation, G5 scorecard

> **ID note**: originally drafted as 2605310100, but that id was concurrently committed by the Covenant Transparency Doctrine ADR in a parallel session. Re-issued as 2605311500 to resolve the collision; all content and verification are unchanged.

**Status**: accepted
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

ADR-2605261800 stood up the kami-engine nv-compat layer; ADR-2605272000
made the isekai Omniverse/PhysX/OpenUSD surface playable (R1.1). At the start
of this session the kami-genesis physics engine supported only two
articulation topologies (Cartpole, DoublePendulum) with closed-form
dynamics, and there was no in-repo, observable answer to a direct user
question: **"how do we know the physics is correct, and how does it line up
with NVIDIA?"**

Two hard constraints frame any answer:

- **Clean-room (ADR-2605261800 §2(b) N1..N9 NEVER)**: NVIDIA Omniverse /
  Isaac Sim / PhysX / Cosmos / Warp may not be linked, vendored, or run in
  religious-corp infra. Therefore a runtime "diff against NVIDIA" is
  impossible by design.
- **Honest claims**: pixel/bit-identical agreement with NVIDIA across
  different algorithms (especially fluids) is not achievable and must never
  be asserted.

The defensible notion of "correct, and consistent with NVIDIA" is therefore:
(A) match the closed-form / conservation-law results that **any** correct
engine — PhysX and Isaac included — must reproduce, and (B) provide a
harness that scores a kami rollout against an NVIDIA Isaac **reference data
file** captured once on an isolated machine (the ADR-2605261600 §G5
procedure: metrics CSV returns, binaries never do).

# Decision

Mature kami-genesis along four axes, each landed with directly-observed
`cargo test` evidence (this session reset and re-did work several times to
keep every committed claim true; only verified states were kept).

## 1. PlanarChain — third World articulation topology (N≥3 serial revolute)

`ArticulationTopology::PlanarChain { state, cfg, links }` generalizes the
engine from cartpole + 2-link to arbitrary N-link serial revolute arms,
backed by the existing reduced-coordinate solver in `planar_chain` (RNEA
bias + CRBA mass matrix + LDLᵀ solve, semi-implicit Euler). `detect_topology`
recognizes a serial revolute chain of N≥3 joints from a parsed URDF and
builds the config from per-joint link mass + length + effort. `step`,
`set_joint_torques`, `joint_positions`, `joint_velocities`, `link_state`
(forward kinematics), and `reset_to_zero` are all N-DOF aware.
`World::jacobian()` dispatches PlanarChain links to the analytic
`planar_chain_link_jacobian`, so all three topologies share one
`get_jacobians()`-shaped surface. New reference URDF
`70-tools/e7m-sim/scenes/arm3/arm3.urdf` exercises the full
parse → detect → solve path.

## 2. Clean-room `isaacsim.core.api` surface (`kami-genesis/src/isaac_api.rs`)

A clean-room mirror of NVIDIA Isaac Sim 4.x's public, documented API so
application code written against Isaac runs unchanged against the KAMI-native
solver, with **no NVIDIA library / header / binary linked or referenced**:

- `IsaacWorld::new(physics_dt)` / `add_articulation` / `step` / `reset`
- `ArticulationView`: `get_joint_positions` / `get_joint_velocities` /
  `num_dof` / `get_jacobian(link) → [6, n_dof]` /
  `get_world_pose(link) → (pos[3], quat_wxyz[4])`
- `ArticulationViewMut::set_joint_efforts` (≈ `apply_action(ArticulationAction)`)

Single-environment (num_envs = 1) at this stage; batched multi-env and the
broader surface (sensor views, DOF-name resolution, batched poses) are
explicitly **not yet implemented** — "complete API parity" is a direction,
not a present claim.

## 3. Validation: analytical solutions + conservation laws

The clean-room evidence that kami agrees with NVIDIA on the **same physics**,
shown without running NVIDIA:

- **kami-genesis** (`planar_chain` tests): uniform rod released horizontal →
  initial α = 3g/(2L) (within 2%); bottom speed ω = √(3g/L) by energy
  conservation (within 2%); frictionless 2-link pendulum energy drift < 5%
  over 3 s (semi-implicit Euler is symplectic → bounded, not secular).
- **kami-dec** (fluid/heat for fire/water/air/wind): pure diffusion
  (decay = 0) conserves Σ T within 0.2% while spreading; decay > 0 strictly
  reduces Σ T each step (never negative); Helmholtz projection drives the
  squared-divergence L2 below 20% of the unprojected field (∇·u ≈ 0).

## 4. G5 Isaac-reference scorecard (`kami-genesis/tests/g5_scorecard.rs`)

The ADR-2605261600 §G5 quantitative gate as a reusable harness: load a
reference trajectory CSV (schema `step,x,x_dot,theta,theta_dot`), run the
matching kami rollout, score `= 1/(1 + rmse/rms_ref)` over the pole DOFs,
gate at ≥ 0.75. The loader **prefers `reference_freefall_isaac.csv`**
(NVIDIA Isaac ground truth, captured once on the isolated trial machine —
metrics CSV only) and falls back to `reference_freefall_analytic.csv` (a
committed stand-in regenerated from the kami closed-form output, clearly
labelled NOT NVIDIA, self-consistency score 1.0). **Dropping in the Isaac CSV
activates the real ≥0.75 gate with zero code change.**

# Consequences

**Positive**

- kami-genesis covers N-link arms, not just cartpole/2-link — the engine
  basis for giemon-class manipulators and future robot articulations.
- Application code can be written to the Isaac surface and run on the
  KAMI-native solver, honoring N1..N9 NEVER.
- "Is it correct?" now has an in-repo, runnable, honest answer (analytical +
  conservation law), and "does it match NVIDIA?" has a ready harness that
  needs only the offline Isaac CSV.

**Negative / honest limitations**

- Isaac surface is single-env and partial; sensor views and batched APIs are
  unimplemented.
- The real NVIDIA cross-check is latent until an Isaac reference CSV is
  captured and committed; today's G5 score is self-consistency (1.0) against
  the analytic stand-in, not against NVIDIA.
- Fluid agreement is conservation-law level only; pixel-identical match with
  NVIDIA Flow / PhysX-fluid is impossible across different algorithms and is
  not claimed.

# Verification (directly observed)

- `cargo test -p kami-genesis` → **87 passed; 0 failed** (CARGO_EXIT=0),
  including PlanarChain detection/FK/Jacobian, isaac_api lifecycle/pose/reset,
  analytical α=3g/2L and ω=√(3g/L) and energy-drift, and the G5 scorecard
  (3 tests, `[G5] score=1.0000`).
- `cargo test -p kami-dec --lib` → **9 passed; 0 failed**, including the three
  conservation-law tests.

Commits (branch `feat/kami-genesis-planar-chain-articulation`):
`11462db08` PlanarChain topology · `e9d55c580` Jacobian wiring ·
`24bdf8bbb` isaac_api surface · `678fdd384` analytical validation ·
`245d5ed5a` kami-dec conservation laws · `eef378cd3` G5 scorecard harness.

# Alternatives Considered

1. **Run NVIDIA Isaac alongside for a live diff.** Rejected — constitutional
   N1..N9 NEVER (ADR-2605261800 §2(b)); also commercial-license + GPU-infra
   barred. The offline-CSV G5 path is the sanctioned substitute.
2. **Claim NVIDIA-equivalence from API parity alone.** Rejected — API shape
   match is not numerical correctness; the analytical/conservation tests and
   the G5 gate are the actual evidence.
3. **Defer fluid validation until a full NS benchmark suite exists.**
   Rejected — conservation laws (mass, monotone decay, incompressibility) are
   cheap, exact, and the correct first gate; richer benchmarks layer on later.

# References

- ADR-2605261800 (NVIDIA Omniverse stack API-compat; §2(b) N1..N9 NEVER)
- ADR-2605261600 (e7m-sim robotics simulation substrate; §G5 quality gate)
- ADR-2605272000 (isekai Omniverse/PhysX/OpenUSD R1.1 playable)
- `40-engine/kami-engine/kami-genesis/src/{planar_chain,world,isaac_api}.rs`
- `40-engine/kami-engine/kami-genesis/tests/g5_scorecard.rs`
- `40-engine/kami-engine/kami-dec/src/lib.rs` (conservation-law tests)
- `70-tools/e7m-sim/scenes/{arm3/arm3.urdf, cartpole/reference_freefall_analytic.csv}`
