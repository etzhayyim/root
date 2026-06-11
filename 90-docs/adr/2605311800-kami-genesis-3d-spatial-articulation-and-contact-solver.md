---
id: adr-2605311800-kami-genesis-3d-spatial-articulation-and-contact-solver
title: "ADR-2605311800: kami-genesis 3-D spatial articulated-body dynamics + rigid contact solver — clean-room PhysX/Isaac-class arm"
status: accepted
doc_type: adr
topic: kami-genesis-3d-spatial-and-contact
authoritative: true
last_verified: 2026-05-31
priority: 5.5
axis: architecture
weight: 0.5
priority_note: "Session record for the arm-quality maturation loop: generalizes kami-genesis from the planar single-axis solver to a full 3-D reduced-coordinate spatial-vector solver (Featherstone RNEA + CRBA, the algorithm class PhysX's Articulation uses) plus a rigid contact/collision solver (sequential-impulse PGS over the CRBA Delassus operator, Coulomb friction), loads a real 6-DOF arm from URDF, drives it through the clean-room Isaac surface, and renders it in giemon.htm. All claims verified by direct cargo-test observation; the decisive gate is an exact planar cross-check against the independently-validated planar_chain solver."
authoritative_for:
  - kami-genesis 3-D spatial-vector articulation solver (arbitrary-axis revolute/prismatic/fixed)
  - kami-genesis rigid contact/collision solver scope and coupling to the articulation
  - giemon physics-arm = 6-DOF URDF-driven 3-D arm (supersedes the planar reconstruction)
  - Spatial3d topology routing in world.rs/isaac_api (mixed-axis chains → 3-D solver)
depends_on:
  - adr-2605311500-kami-genesis-physics-validation-and-isaac-clean-room-surface
  - adr-2605261800-nvidia-omniverse-stack-api-compat
  - adr-2605261600-robotics-simulation-substrate-r0
related:
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
supersedes: []
superseded_by: []
---

# ADR-2605311800: kami-genesis 3-D spatial articulation + rigid contact solver

**Status**: accepted
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

ADR-2605311500 matured kami-genesis to N-link **planar** (single shared
rotation axis) reduced-coordinate dynamics with a clean-room `isaacsim.core.api`
surface and analytic/conservation validation. The giemon.htm "physics-arm" was
a planar chain.

The user asked for the arm to be designed/implemented "more properly — to
Omniverse / PhysX / Isaac Sim equivalent quality", and chose the scope that
**also** includes a contact/collision solver. Two hard constraints stand
(ADR-2605261800 §2(b), N1..N9 NEVER): no NVIDIA Omniverse / Isaac / PhysX /
Warp / Cosmos code may be linked, vendored, or run. "Equivalent quality"
therefore means a **clean-room native implementation of the same algorithm
class** — for articulations that is reduced-coordinate Featherstone spatial
dynamics (what PhysX's `Articulation` uses); for contact it is a velocity-level
sequential-impulse solver with a Coulomb friction cone (the TGS approach class).

# Decision

Add a full 3-D engine to kami-genesis, validated each step by directly-observed
`cargo test`, and wire it end-to-end into the giemon arm and the Isaac surface.

## 1. Spatial-vector algebra — `kami-genesis/src/spatial.rs`

6-D Plücker algebra as explicit 6×6 matrices / 6-vectors: motion/force vectors,
`plucker(E,r)` coordinate transforms (+ inverse), `spatial_inertia(m,c,Iᶜ)`,
and the motion/force cross-products `crm`/`crf`. Dense form (cost is irrelevant
at n ≤ ~8 DOF) chosen for verifiability. 4 unit tests (cross-product identity,
transform round-trip, point-mass momentum, `crf = −crmᵀ`).

## 2. 3-D reduced-coordinate solver — `kami-genesis/src/articulation3d.rs`

Forward dynamics `M(q)·q̈ = τ − C(q,q̇) − g(q)` with **RNEA** bias (Featherstone
Table 5.1, gravity injected as base acceleration), **CRBA** joint-space inertia
(Table 6.2), in-place `LDLᵀ` solve, semi-implicit (symplectic) Euler. Handles
**arbitrary-axis** revolute / prismatic / fixed joints in a tree, with joint
limits, viscous damping, and effort clamps. Provides 3-D forward kinematics,
geometric Jacobians, and a URDF builder (`from_articulated_system`).

**The decisive correctness gate**: a planar chain built in the 3-D solver
reproduces the independently-validated `planar_chain` `q(t)` trajectory for
n = 1..4 within 2e-3 over 0.5 s. Plus: single-pendulum energy-bounded, and a
genuinely 3-D arm (axes z, y, x) conserving energy under no gravity (proving
off-plane motion is handled).

## 3. Rigid contact/collision solver — `kami-genesis/src/contact.rs`

Sphere/capsule colliders on links vs a static ground plane → velocity-level
**sequential-impulse / projected Gauss-Seidel** in the articulation's joint
space. The contact-space inverse mass is the Delassus operator
`A = Jₖ M⁻¹ Jₖᵀ`, reusing the CRBA `M` and the link point-Jacobian. Coulomb
friction cone (`|λt| ≤ μ λn`), Baumgarte penetration correction, restitution
(default 0). Coupled into a `step`: predict free velocity → generate contacts →
PGS solve → integrate positions. 3 tests: a link settles **on** the ground (no
runaway penetration, comes to rest), no false contacts when the ground is far,
and contact never injects energy.

## 4. Engine wiring — `world.rs` + `isaac_api.rs`

New `ArticulationTopology::Spatial3d` is the general fallback in
`detect_topology`: cartpole / double-pendulum / **all-parallel-axis** planar
chains keep their existing solvers; any other URDF (e.g. a mixed-axis arm)
routes to the 3-D solver. `step` / `set_joint_torques` / `reset` /
`joint_positions` / `joint_velocities` / `jacobian` (6×n geometric) /
`link_state` (world pose + spatial velocity) all dispatch `Spatial3d`. The
clean-room `IsaacWorld` / `ArticulationView` surface therefore drives a real
6-DOF arm unchanged (`num_dof`, `set_joint_efforts`, `get_joint_positions`,
`get_world_pose`, `get_jacobian`).

## 5. Real 6-DOF giemon arm — URDF + 3-D render

`70-tools/e7m-sim/scenes/giemon_arm6/giemon_arm6.urdf` — a fixed-base 6-DOF
manipulator (axes z, y, y, z, y, z; per-joint mass/inertia/limit/damping). The
giemon app parses it at runtime (`kami_articulated::parse_urdf`), builds the
3-D config, and simulates it with the contact solver against a ground plane.
giemon.htm physics-arm is now **Arm6 — 3-D Physics Sim**: keys 1–6 select a
joint, J/L torque it. Replaces the planar reconstruction (ADR-2605311500 era).

# Consequences

**Positive**

- kami-genesis now does genuine 3-D, arbitrary-axis, reduced-coordinate
  articulation dynamics — the basis for real manipulators and legged robots —
  plus rigid contact, the two pieces that compose (CRBA `M` is the contact
  Delassus operator).
- Application code written to the Isaac `Articulation` API drives a 6-DOF arm
  on the KAMI-native solver, honoring N1..N9 NEVER.

**Negative / honest limitations**

- Contact is link-vs-static-ground (sphere/capsule); **self-collision broad/
  narrow phase and dynamic-vs-dynamic contact are not yet implemented**.
- Single-environment; no GPU-batched envs (the WGSL path remains cartpole-only).
- No closed loops (tree topologies only), no joint-limit restitution, no
  articulated soft bodies / fluids — those are separate efforts.
- "PhysX/Isaac-equivalent" is a claim about the **algorithm class and the
  validated articulation+contact core**, not bit-identical agreement (which is
  impossible across different implementations and never asserted, per
  ADR-2605311500).

# Verification (directly observed)

- `cargo test -p kami-genesis` → **92 passed; 0 failed**, including the planar
  cross-check (3-D solver == planar_chain, n=1..4), single-pendulum energy,
  3-D no-gravity energy conservation, contact settle/no-penetration/no-energy-
  injection, and `isaac_world_drives_6dof_arm_via_spatial_solver`.
- `cargo test -p kami-app-giemon` → **4 passed** (URDF loads as 6-DOF,
  arm steps under gravity, link segments well-formed).
- `wasm-pack build kami-app-giemon --target web --release` → ok; exports
  `run_giemon_sim_v1` + `giemonSetJointTorque` + `giemonSelectJoint`.

# Alternatives Considered

1. **Articulated Body Algorithm (ABA, O(n)) instead of CRBA+RNEA (O(n³)).**
   Rejected for this pass — at n ≤ ~8 the cubic cost is irrelevant, and
   CRBA+RNEA reuses the validated planar pattern and yields `M` explicitly,
   which the contact solver needs as the Delassus operator. ABA is a future
   optimization.
2. **Maximal-coordinate (per-body 6-DOF + constraints) like a generic rigid
   solver.** Rejected — reduced coordinates are what PhysX `Articulation` /
   Isaac use for manipulators (no drift, exact joints), matching the target.
3. **Keep the planar arm and just add more joints.** Rejected — not 3-D, not
   "equivalent quality".

# References

- ADR-2605311500 (planar maturation + Isaac surface + validation strategy)
- ADR-2605261800 (NVIDIA stack API-compat; §2(b) N1..N9 NEVER)
- Featherstone, *Rigid Body Dynamics Algorithms* (2008), Tables 5.1 / 6.2
- `40-engine/kami-engine/kami-genesis/src/{spatial,articulation3d,contact,world,isaac_api}.rs`
- `70-tools/e7m-sim/scenes/giemon_arm6/giemon_arm6.urdf`
- `40-engine/kami-engine/kami-app-giemon/src/lib.rs` (run_giemon_sim_v1)
