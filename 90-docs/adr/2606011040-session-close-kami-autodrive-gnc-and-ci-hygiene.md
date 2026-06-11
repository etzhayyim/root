---
id: adr-2606011040-session-close-kami-autodrive-gnc-and-ci-hygiene
title: "ADR-2606011040: Session close — kami-autodrive GNC autonomy layer + CI-hygiene green"
status: active
doc_type: adr
topic: session-close-kami-autodrive-gnc
authoritative: true
last_verified: 2026-06-01
priority: 5.0
axis: architecture
weight: 0.5
priority_note: "Operational close for the 2026-06-01 kami-autodrive vertical: the previously-missing autonomy (perception→planning→control) layer for kami-engine landed on main as a 74-test crate driving all four vehicle classes (car/ship/drone/aircraft) on real physics plants, plus the registry + monorepo-health CI debt this work surfaced (and that ADR-2605312355 had flagged red) was driven to green. Honest follow-ups recorded: the Shibuya contact-physics agent autonomy needs a dedicated trajectory-tracking controller (straight-line drive works; arbitrary-goal/detour capture of the heavy free-yaw base does not under the kinematic autopilot)."
authoritative_for:
  - kami-autodrive crate landing (4 PRs) + per-class fidelity boundary
  - CI-hygiene resolution (docs-registry sync, dependabot defunct, sdk-exports un-built skip)
depends_on:
  - adr-2606010600-kami-autodrive-gnc-autonomy-layer
  - adr-2605242000-wadachi-autonomous-mobility-rd
related:
  - adr-2605312355-session-close-kotoba-datom-first-class-and-charter-rider-d1
  - adr-2605261800-nvidia-omniverse-compat-facade
  - adr-2605311900-shibuya-street-digital-twin-osm-citymesh-fullphysics-sim
supersedes: []
superseded_by: []
---

# ADR-2606011040: Session close — kami-autodrive GNC autonomy layer + CI-hygiene green

**Status**: active
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

An audit of "how far is autonomous driving designed/implemented for car / drone /
ship / aircraft?" found kami-engine had every building block — `kami-vehicle`
(BeamNG-grade soft-body car), `kami-sensor-sim` (lidar/camera/IMU, Isaac-Sim-API
compatible), `kami-pathfind` (A*) — but **no autonomy loop**: `kami-app-car-sim`
was JS-manual and the Shibuya agents followed a scripted sinusoidal steer with no
perception/planning/control. This is the same gap NVIDIA Omniverse / Isaac Sim
has — the simulator provides the plant + sensors; the AV stack is a separate
layer the integrator supplies.

# Decision

Land **`40-engine/kami-engine/kami-autodrive`** (ADR-2606010600) — a
plant-agnostic guidance/navigation/control crate closing
`lidar/camera → occupancy grid → A* → pure-pursuit + PID → Command → plant`,
and drive the surfaced CI debt to green.

Merged to `main` (5 PRs):

- **#308** `kami-autodrive` — GNC core; all four `VehicleClass` driven by one
  Autopilot with **real physics plants**: `kami-vehicle` soft-body car /
  `BicycleModel`; `ShipHydro` (Fossen 3-DOF hydrodynamics); `Multirotor` (rotor
  thrust-vector + aero drag); `FixedWing` (lift/drag, ISA density, stall,
  bank-to-turn loiter). Multi-modal perception (lidar + depth-camera fusion),
  dynamic obstacles, multi-agent `Fleet` (priority right-of-way + head-on lane
  discipline + 4-way intersection), dead-reckoning `StateEstimator`, collision-
  validated path smoothing, determinism + criterion benches, doc-tests.
  **74 tests; clippy clean.** Apache/MIT, CPU-runnable, nv-compat `isaacsim`.
- **#310** docs-registry sync (registers ADR-2606010600 + 4 base-drift docs;
  docs.json/graph.jsonld 721→726).
- **#311** dependabot: drop the defunct `/50-infra/l2-anchor-contract/lib/forge-std`
  entry (directory gone).
- **#544** `sdk-exports-dist` audit: skip un-built packages (export targets
  resolve into git-ignored `dist/`; CI doesn't build, so a fresh checkout falsely
  flagged every kami-engine-sdk export — now a no-op pre-build, still catches
  real mismatches once `dist/` exists).

# Consequences

- The autonomy-PR-related CI is **green**: `docs-registry-freshness`,
  `dependabot-defunct`, `sdk-exports-dist`, subrepo-stale (7 = baseline),
  `lint-and-test` all pass on `main` — resolving the pre-existing audit-health
  debt that ADR-2605312355 had explicitly recorded as red (forge-std,
  sdk-exports `./dist/*`, stale subrepo URLs).
- `kami-autodrive` is plain monorepo source (a `040000 tree`, **not** a
  submodule or git-subrepo). For reference: `kami-engine-sdk` is the one
  git-subrepo here (`.gitrepo` → github.com/etzhayyim/kami-engine-sdk,
  method=merge), and `kami-engine` itself is plain monorepo source.
- Simulation/design substrate only — real-world deployment routes through
  `wadachi` (ADR-2605242000): SAE L4 ceiling, Transparent-Force gated.

## Honest follow-ups (deferred)

- **Shibuya agent autonomy**: wiring `kami-autodrive` into the `kami-app-shibuya`
  contact-physics agents is feasible (it compiles; a heading-PD controller drives
  the floating base straight to an open goal), but the heavy free-yaw contact
  body does **not** reliably capture arbitrary goals or execute sharp building
  detours under the kinematic autopilot — it needs a dedicated trajectory-tracking
  controller. Two clean-abandoned attempts; `main` untouched.
- Non-car plants are 3-DOF reduced-order (not 6-DOF CFD); dense multi-agent
  gridlock can still stall; reverse K-turn recovery is opt-in.

# Alternatives Considered

- Activate `wadachi` cells directly — rejected: governance-gated actor cells, not
  a reusable engine library; the GNC math belongs in kami-engine.
- Adopt NVIDIA Isaac/DRIVE Sim — rejected: closed-source + commercial-GPU
  coupling conflicts with Charter Rider §2(i); kami-autodrive keeps the
  `nv-compat` API shape while staying Apache/MIT and CPU-runnable.

# References

- `40-engine/kami-engine/kami-autodrive/` (crate + README + 17 test files)
- ADR-2606010600 (kami-autodrive GNC design)
- ADR-2605242000 (wadachi), ADR-2605261800 (nv-compat facade)
- ADR-2605312355 (prior session close — recorded the audit-health debt now resolved)
