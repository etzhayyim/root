---
id: adr-2606010600-kami-autodrive-gnc-autonomy-layer
title: "ADR-2606010600: kami-autodrive — vehicle-class-agnostic GNC autonomy layer (perception → planning → control)"
status: accepted
doc_type: adr
topic: kami-autodrive-gnc-autonomy
authoritative: true
last_verified: 2026-05-31
priority: 5.5
axis: architecture
weight: 0.5
priority_note: "Closes the missing autonomy loop in kami-engine: the simulation primitives (kami-vehicle BeamNG-grade car dynamics, kami-sensor-sim lidar/camera/IMU, kami-pathfind A*) already existed in isolation but were never wired into a perception→planning→control stack. kami-autodrive is that wiring — a plant-agnostic guidance/navigation/control crate that drives both a kinematic bicycle plant (shared by ship/drone/aircraft at planar fidelity) and the real soft-body sedan (car, full fidelity) to a goal while avoiding lidar-sensed obstacles. Analogous to the AV stack that rides on NVIDIA Isaac Sim / DRIVE Sim. Honest fidelity boundary: only the car has a high-fidelity dynamics plant today; the other three classes are planar-kinematic."
authoritative_for:
  - kami-autodrive crate API (Autopilot, perception/OccupancyGrid, planner, control, plant, classes)
  - lidar→occupancy→A*→pure-pursuit+PID closed loop wiring over kami-sensor-sim + kami-pathfind
  - SoftBodyCar adapter (kami-vehicle plant driven by the same Autopilot; soft-body-car feature)
  - per-VehicleClass kinematic fidelity boundary (Car full / Ship·Drone·Aircraft planar-kinematic)
depends_on:
  - adr-2605261800-nvidia-omniverse-compat-facade
  - adr-2605242000-wadachi-autonomous-mobility-rd
related:
  - adr-2605311900-shibuya-street-digital-twin-osm-citymesh-fullphysics-sim
  - adr-2605311800-kami-genesis-3d-spatial-articulation-and-contact-solver
supersedes: []
superseded_by: []
---

# ADR-2606010600: kami-autodrive — vehicle-class-agnostic GNC autonomy layer

**Status**: accepted
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

An audit of "how far is autonomous driving designed/implemented for car / drone /
ship / aircraft?" found that kami-engine already had every **building block** but
no **autonomy loop**:

- **Plant (dynamics)**: `kami-vehicle` — BeamNG-grade soft-body car (Pacejka
  tire, full powertrain, ~80 nodes / ~250 beams, 2 kHz substep). `kami-genesis`
  — rigid/articulated 3-D contact solver.
- **Sensors**: `kami-sensor-sim` — lidar (VLP-16 intrinsics, analytic ray
  intersection), pinhole camera, IMU, contact; Isaac-Sim-4.x-API compatible.
- **Search**: `kami-pathfind` — A* grid + NavMesh.
- **Scenes**: Shibuya digital twin (OSM citymesh + Mapillary SfM splat).

But the pieces were **never connected**. `kami-app-car-sim` is *manually* driven
from JS (`window.__carsim_*`). The Shibuya agents follow a **scripted sinusoidal
steer** (`tau[3] = 200·sin(t·0.6 + phase) − …`) with **no perception, no
planning, no control**. The `wadachi` actor (ADR-2605242000) defines the
constitutional envelope (SAE L4 ceiling, Transparent Force gating) but its cells
are R0 stubs that raise `RuntimeError`.

This is structurally the same gap NVIDIA Omniverse / Isaac Sim has: the simulator
supplies the **plant + sensors + synthetic data**; the **autonomy stack
(perception → planning → control)** is a separate layer the integrator must
provide. We were missing that layer.

# Decision

Introduce **`40-engine/kami-engine/kami-autodrive`** — a plant-agnostic
guidance/navigation/control (GNC) crate that closes the loop:

```
lidar sweep ─▶ perception (occupancy grid) ─▶ planner (A*) ─▶
pure-pursuit + PID control ─▶ Command ─▶ plant ─▶ (new pose) ─▶ …
```

Modules:

- **`types`** — `Pose2` (z-up, ROS REP-105 planar `(x,y)` + yaw), `Command`
  (normalised throttle/brake/steer/handbrake mirroring `kami_vehicle::Controls`).
- **`classes`** — `VehicleClass {Car, Ship, Drone, Aircraft}` → `VehicleLimits`
  (max speed/accel/decel, wheelbase, max steer, footprint radius).
- **`perception`** — `OccupancyGrid` ingests `kami_sensor_sim::LidarReturn`
  sweeps (sensor-frame height-band filtered to reject the ground/overhead),
  configuration-space `inflated()` by footprint, `to_cost_grid()` for the
  planner; plus `forward_clearance()` for reactive braking.
- **`planner`** — A* over the inflated grid via `kami-pathfind`, returned as a
  line-of-sight-simplified world polyline.
- **`control`** — `PurePursuit` lateral controller + `SpeedController` (PID)
  longitudinal + curvature speed limit.
- **`plant`** — `Plant` trait (the GNC↔body seam) + `BicycleModel` kinematic
  plant.
- **`autopilot`** — `Autopilot` ties it together with a `DriveState` machine
  (Idle/Cruise/Slow/Stop/Blocked/Arrived): ingest → emergency-stop check →
  (re)plan → pure-pursuit steer → speed target (min of cruise/curvature/obstacle
  caps).
- **`vehicle_adapter`** (feature `soft-body-car`) — `SoftBodyCar` wraps a real
  `kami_vehicle::Vehicle` as a `Plant`, mapping the y-up vehicle frame to the
  z-up planar autonomy frame, so the **same `Autopilot` drives the BeamNG-grade
  sedan**.

## Fidelity (all four classes now have a real physics plant)

| Class | Guidance/Nav/Control | Dynamics plant |
|---|---|---|
| **Car** | full GNC loop | `kami-vehicle` soft-body (`soft-body-car`) / `BicycleModel` ✅ |
| **Ship** | full GNC loop | `dynamics::ShipHydro` — Fossen 3-DOF (surge/sway/yaw, added mass, quadratic damping, speed-dependent rudder, turn-induced sway) ✅ |
| **Drone** | full GNC loop | `dynamics::Multirotor` — thrust-vector tilt + quadratic aero drag + yaw-rate + sideslip damping; can hover ✅ |
| **Aircraft** | full GNC loop | `dynamics::FixedWing` — thrust, parasitic+induced drag, lift, ISA air density, `C_Lmax` stall, coordinated bank-to-turn ✅ |

The autonomy stack is shared across all four; each `Plant` is swappable with
**zero change** to perception/planning/control. The pursuit controller is
decoupled from any bicycle wheelbase (it scales path curvature by a per-class
`turn_radius_ref`) so a rudder ship, a banking aircraft, and a yawing multirotor
all steer correctly from the same law.

Reduced-order caveats (HONEST): the ship/aircraft/drone plants are 3-DOF
point/coordinated-turn models, not full 6-DOF CFD; the aircraft holds cruise
altitude and **cannot hover** (it overflies a goal, since min controllable speed
= stall) — and after an overshoot a fixed-wing needs a loiter/procedure-turn
pattern (deferred). The ship/drone slow to rest at the goal via an approach
deceleration profile.

# Consequences

- First end-to-end **autonomous** driving in the repo (vs. manual `car-sim` and
  scripted Shibuya agents), across **all four vehicle classes with real physics
  plants**. Verified by tests, all green (9):
  - `reaches_goal_on_open_ground`, `routes_around_a_blocking_obstacle`,
    `emergency_stops_for_a_sudden_wall`, `ship_with_wide_turns_still_arrives`,
    `lidar_ingest_marks_occupancy` (kinematic plant, default features);
  - `ship_hydrodynamics_turns_and_arrives` (asserts turn-induced sway),
    `fixed_wing_flies_above_stall_to_goal` (asserts above-stall flight),
    `multirotor_tilts_to_translate_and_hovers_at_goal` (asserts thrust tilt +
    near-hover at goal) — the high-fidelity hydro/aero/rotor plants under the
    same Autopilot;
  - `soft_body_sedan_drives_to_waypoint` (`--features soft-body-car`: the
    real soft-body sedan autonomously reaches a waypoint).
  - `examples/drive_to_goal.rs`: a car detects a wall at x∈[18,22], routes to
    y≈6.7 around it, and arrives at (40, 0).
- Provides the concrete substrate the `wadachi` R1 cells (ADR-2605242000) can
  call once Council-ratified; this crate is **simulation/design only** and a
  fielded deployment remains SAE-L4-ceiling + Transparent-Force gated.
- Next steps (deferred): wire the Shibuya splat/citymesh as the `Scene` so agents
  perceive the real street; camera-based perception (`kami-sensor-sim::Camera`);
  multi-agent (agent-agent avoidance); fixed-wing loiter/procedure-turn for
  re-approach; full 6-DOF CFD-grade marine/aero plants; Hybrid-A* / lattice
  planner for kinodynamic constraints.

# Alternatives Considered

- **Activate `wadachi` cells directly** — rejected: those are governance-gated
  LangGraph actor cells, not a reusable engine library; the GNC math belongs in
  kami-engine, callable by wadachi.
- **One monolithic per-class stack** — rejected: duplicates perception/planning;
  the `Plant` trait keeps one GNC loop across classes.
- **Adopt NVIDIA Isaac Sim / DRIVE Sim** — rejected for the religious-corp
  substrate: closed-source + commercial-GPU coupling conflicts with the Charter
  Rider §2(i) no-commercial-GPU and open-source invariants. `kami-autodrive`
  keeps the `nv-compat` API shape (`isaacsim` target) while staying Apache/MIT
  and CPU-runnable.

# References

- `40-engine/kami-engine/kami-autodrive/` — crate (src + tests + example)
- ADR-2605242000 — wadachi autonomous-mobility R&D (constitutional envelope)
- ADR-2605261800 — NVIDIA Omniverse compat facade (`kami-sensor-sim` lineage)
- ADR-2605311900 — Shibuya street digital twin (target Scene)
