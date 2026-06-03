---
id: adr-2605311900-shibuya-street-digital-twin-osm-citymesh-fullphysics-sim
title: "ADR-2605311900: Shibuya street digital-twin — OSM → city mesh → kami-genesis full-physics multi-agent sim (iteration 1)"
status: accepted
doc_type: adr
topic: shibuya-street-digital-twin
authoritative: true
last_verified: 2026-05-31
priority: 5.5
axis: architecture
weight: 0.5
priority_note: "Turns a real Shibuya Scramble OSM block into a 3-D physics simulation: an offline Overpass→scene preprocessor, a static building-AABB / road-ground collision substrate, and multiple 4-DOF floating-base agents doing full physics (gravity + ground + building collision + Coulomb friction) on the kami-genesis 3-D spatial solver. Iteration 1; verified by direct cargo-test. Honest deferrals listed (BeamNG-vehicle integration, agent-agent collision, polygon-accurate building collision, PLATEAU LOD2, autonomous-driving stack)."
authoritative_for:
  - OSM→e7m-sim city-scene format (osm_to_citymesh.py) and the Shibuya snapshot
  - kami-app-shibuya full-physics multi-agent street sim (iteration 1)
  - floating-base agent model (4-DOF x/y/z + yaw via URDF) on the kami-genesis solver
depends_on:
  - adr-2605311800-kami-genesis-3d-spatial-articulation-and-contact-solver
  - adr-2605261600-robotics-simulation-substrate-r0
related:
  - adr-2605262500-robotics-world-data-ingestion-and-usd-pipeline
supersedes: []
superseded_by: []
---

# ADR-2605311900: Shibuya street digital-twin — OSM → full-physics sim (iter 1)

**Status**: accepted
**Date**: 2026-05-31
**Deciders**: Jun Kawasaki

# Context

ADR-2605311800 landed the kami-genesis 3-D spatial articulated-body solver +
rigid contact (incl. static `Obstacle::Plane`/`Aabb`). The ask: take **real
Shibuya streets**, build a 3-D model, and run a **full-physics, multi-agent**
simulation on it (chosen scope: OSM source + multiple agents + full physics).

Map-source / substrate constraints already in the repo: external MVT/tracking
is barred (maps app §); OSM is the application-consumed, ODbL-permitted source
(deps.toml). The contact solver is articulation-based (fixed-base), so a mobile
street agent needs a free base.

# Decision

Ship iteration 1 of a Shibuya digital twin, each piece verified by `cargo test`.

## 1. OSM → city scene (offline, reproducible)

`70-tools/scripts/sim/osm_to_citymesh.py` projects an Overpass `out geom`
extract into local ENU metres (origin = bbox centre, z-up) and emits a compact
scene JSON: per-building footprint **AABB + height**, road **polylines + width**,
and the bbox. Committed inputs/outputs for the Shibuya Scramble block
(`70-tools/e7m-sim/scenes/shibuya/`): `shibuya_scramble.osm.json` (raw, 144
buildings + 318 roads) and `shibuya_scramble.scene.json` (~35 KB, baked).
Building height = `height` tag → `building:levels×3.3` → 12 m default.

## 2. Collision substrate

- Buildings → static `kami_genesis::Obstacle::Aabb` (footprint × [0, height]).
- Road network → the drivable ground plane (`ContactParams::ground_z = 0`) plus
  a ribbon render. (Per-building footprint *polygon*-accurate collision and DEM
  terrain are deferred; the AABB proxy is the iteration-1 collision model.)

## 3. Floating-base agents (`kami-app-shibuya`)

Each agent is a **4-DOF floating base** — x/y/z prismatic + yaw `continuous` —
built as a tiny generated URDF and loaded through the validated
`Articulation3dConfig::from_articulated_system` path (intermediate links
~massless; the body link carries box mass + inertia). It carries 8 corner
sphere colliders and its own `ContactWorld` (ground + all building AABBs). A
simple controller applies a forward drive force along the heading + drag +
gentle wandering steer; gravity + contact do the rest. Multiple agents run
independently against the shared static city (agent-agent collision deferred).

The renderer is y-up and the sim is z-up, so the whole scene is rotated −90°
about X. Static geometry (ground / roads / low + tall buildings) is merged into
a few batches; agents re-bake their body box under the FK transform each frame.
Entry `run_shibuya_v1(canvas)`, page `shibuya.htm`.

# Consequences

**Positive**

- A real Shibuya block is now a 3-D, full-physics sandbox: agents fall onto the
  road, rest under gravity + friction, drive, and are stopped by real building
  footprints — all on the clean-room kami-genesis engine.
- The OSM→scene tool generalizes to any bbox/city (swap the Overpass extract).

**Negative / honest limitations (iteration 1)**

- Buildings collide as **AABBs**, not true footprint polygons; ground is a flat
  plane (no DEM slope). Shibuya's real elevation/footprint detail is a follow-up.
- Agents are **rigid box bodies on a 4-DOF base** (translate + yaw): no pitch/
  roll, no tire/suspension model. BeamNG-grade `kami-vehicle` integration and a
  wheeled/legged articulated agent are deferred.
- **Agent-agent collision is not solved** (each agent vs the static world only).
- No sensors / planning (autonomous-driving stack deferred); PLATEAU LOD2 meshes
  deferred.

# Verification (directly observed)

- `cargo test -p kami-app-shibuya` → **4 passed; 0 failed**: scene loads
  (144 buildings / 318 roads), agent is 4-DOF, agent dropped from z=3 **settles
  on the road** (no penetration, comes to rest), and an agent driving into a
  building **AABB is blocked** (no tunnelling).
- `wasm-pack build kami-app-shibuya --target web --release` → ok; export
  `run_shibuya_v1`.
- `cargo test -p kami-genesis` remains **94 passed; 0 failed** (obstacle support).

# Alternatives Considered

1. **Google Photorealistic 3D Tiles / PLATEAU as the source.** Deferred — OSM is
   in-repo, ODbL, no external key/tracking; PLATEAU LOD2 is a strong follow-up
   for true building shells.
2. **Maximal-coordinate free rigid bodies for agents.** Rejected for iter 1 —
   the 4-DOF floating-base articulation reuses the validated solver + contact
   path with no new dynamics code.
3. **Per-segment road draw calls.** Rejected — merged into a few batches to keep
   the static scene at a handful of draw calls.

# References

- ADR-2605311800 (kami-genesis 3-D spatial solver + contact + `Obstacle`)
- `70-tools/scripts/sim/osm_to_citymesh.py`
- `70-tools/e7m-sim/scenes/shibuya/{shibuya_scramble.osm.json, .scene.json}`
- `40-engine/kami-engine/kami-app-shibuya/src/lib.rs`
- `60-apps/etzhayyim-project-isekai/appview/.../svelte/static/shibuya.htm`
