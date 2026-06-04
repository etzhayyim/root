---
id: adr-2605252615-kusawake-autonomous-agri-mobile-r0
title: "ADR-2605252615: Kusawake (草分け) — Autonomous Agri-Mobile Platform R0 (swagbot-class wheeled robot; mfg = suki Wave 2; ops = mitsuho.harvest_robotics; sim = e7m-sim)"
status: proposed
doc_type: adr
topic: kusawake-autonomous-agri-mobile-r0
authoritative: true
last_verified: 2026-05-25
priority: 5.5
axis: architecture
weight: 0.55
authoritative_for:
  - Kusawake robot class identity (name, manufacturer, operator, scope) — R0 reservation
  - Autonomous wheeled agri-platform constitutional gates G1..G10 + non-goals N1..N8
  - Manufacturer binding to suki Wave 2 (orchard/vineyard <50 hp electric carve-out, ADR-2605261500)
  - Operator binding to mitsuho.harvest_robotics + new mitsuho.autonomous_mobile cell (ADR-2605261015)
  - Simulation binding to e7m-sim per ADR-2605261600 (R1 = MuJoCo MJX + Vulkan RT + OpenUSD; Omniverse/Isaac Sim N3 NEVER)
  - R0..R3 phased roadmap (R0 charter / R1 single-unit field PoC / R2 fleet ≤5 unit / R3 community-scale ≤30 unit)
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605261015
  - adr-2605261500-suki-farm-tractor-tier-b-actor-r0
  - adr-2605261600-robotics-simulation-substrate-r0
related:
  - 20-actors/mitsuho/manifest.jsonld
  - 20-actors/suki/manifest.jsonld
  - 70-tools/e7m-sim/scenes/kusawake/
supersedes: []
superseded_by: []
---

# ADR-2605252615: Kusawake (草分け) — Autonomous Agri-Mobile Platform R0

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Manufacturer = ADR-2605261500 (suki Wave 2 carve-out). Operator = ADR-2605261015 (mitsuho.harvest_robotics + new autonomous_mobile cell). Sim layer = ADR-2605261600 (e7m-sim). Autonomy stack = ADR-2605242000 (wadachi SAE J3016 framework, capped at Level 3 per suki G12 + N6 farmer-land-relationship preservation).

## Context

religious-corp's existing agricultural robotics fleet (kuni-umi inherited, declared in mitsuho R0 ADR-2605261015 §Robotics Fleet):

| Existing class | Function | Form factor |
|---|---|---|
| Giemon | tractor-equivalent crawler + arm | ≥1 ton crawler |
| Otete | precision tool arm | stationary / arm-mounted |
| Mimi | crop / soil metrology | sensor pod |
| Sora | aerial survey + spot treatment | UAV |
| Tsumugi (R2+) | greenhouse / vertical-farm tending | rail-bound gantry |

**Gap**: no **autonomous wheeled ground platform** class exists for between-row weed control, livestock herding, perimeter scouting, and pasture intervention. Reference precedent in the field: SwagBot (University of Sydney ACFR, 4WD/4WS electric, ~250 kg, livestock + weed-control modes). The functional envelope — wheeled, electric, modular tool deck, ride-skip autonomy on private rangeland/orchard — is methodologically distinct from:

- Giemon (crawler track, ≥1 ton, on-board operator-replaceable; tractor-class)
- Sora (aerial, no ground contact, ≤25 kg, spot only)
- Otete / Tsumugi (non-locomotive)
- suki tractor Wave 1 ≥50 hp diesel/hybrid (mass + fuel envelope wrong for swag-class)

Without this class, mitsuho cannot deliver the weed-control / herd / scout function envelope at scale within the L2 Sustenance gate timeline (ADR-2605261000), and suki Wave 2 (orchard/vineyard <50 hp electric, deferred in ADR-2605261500 §scope) has no constitutional landing pad.

## Decision

Register **Kusawake (草分け)** as a religious-corp robot class:

| Field | Value |
|---|---|
| Class name | `Kusawake` (草分け — "trailblazer / first through the grass") |
| Japanese gloss | 草分け / くさわけ — semantic = pioneer / weed-clearer (dual reading aligns with both swagbot's bush-clearing function and religious-corp first autonomous mobile platform) |
| Manufacturer actor | `suki` (Wave 2 carve-out: orchard/vineyard <50 hp electric per ADR-2605261500 §scope Wave 2) |
| Operator actor | `mitsuho` (new `autonomous_mobile` cell + existing `harvest_robotics` cell consume Kusawake output) |
| Methodology reference | SwagBot (University of Sydney ACFR; published open papers + open photographs). Methodology adopted; closed firmware / vendor lock-in / data-monetization telemetry NOT adopted. |
| Per-unit DID | `did:web:etzhayyim.com:mitsuho:kusawake:<serial>` |
| Constitutional ADR | this ADR (R0) |
| License | Apache 2.0 + Charter Compliance Rider v2.0 (firmware, mech CAD, sensor stack — all open) |

### Wave 1 mechanical envelope (R0–R3 binding)

| Spec | Wave 1 target |
|---|---|
| Drive | 4WD electric (4× ≤2 kW BLDC hub or geared in-hub) |
| Steering | 4WS (Ackermann + crab + spin modes) |
| Battery | LFP swap-pack ≤2 kWh; sodium-ion R2+ qualification |
| Mass | ≤300 kg (with 50 kg payload deck) |
| Footprint | ≤1.4 × 0.9 m (orchard-row clearance ≥2.0 m typical) |
| Speed | road ≤6 km/h; field ≤4 km/h; manual tele-op ≤8 km/h |
| IP rating | IP67 enclosure; brushless ungeared seal |
| Compute | ARM64 or RISC-V open SoC (tsutae ADR-2605261300 SoC pool); bootloader unlock default |
| Sensors | GPS-RTK + IMU + 360° lidar (≤16-line solid-state) + 2× RGB + 1× thermal + 4× ultrasonic; **no always-on cellular / no telemetry sale** |
| Tool deck | ISO-mounted modular (weeding flail / electric trimmer / herd-encourage sound emitter / scouting camera tower) |
| Connectivity | Wi-Fi 6 mesh + LoRa long-range telemetry; **cellular hardware-removable per tsutae G6** |
| Autonomy ceiling | **SAE J3016 Level 3** (driver remote-supervised within RF mesh; never autonomous beyond mesh per suki N6 farmer-land-relationship preservation) |

### Constitutional Gates G1..G10 (IMMUTABLE R0–R3)

- **G1 Open firmware end-to-end**: all motor controllers, sensor drivers, planner, and ROS2 bridge published Apache 2.0 + Charter Rider; no binary blobs except WiFi/cellular modem firmware (vendor-supplied; cellular module hardware-removable per tsutae G6).
- **G2 Right-to-Repair (dual-layer)**: hardware modular (tsutae G3 inheritance — iFixit ≥9/10 target) + firmware re-flash on parts swap NOT vendor-gated (suki G10 inheritance). Replacement parts catalogued openly on IPFS-pinned BoM per VIN-equivalent serial.
- **G3 SAE J3016 Level 3 ceiling**: full autonomy (Level 4/5) is N6 NEVER — preserves farmer-land-relationship (suki G12 + N6 inheritance + ADR-2605192100 §1.13 wellbecoming).
- **G4 Witness quorum** (ADR-2605191524): every field-intervention record (weed cut / herd nudge / scouting capture) requires Ed25519 sigs from ≥2 distinct sources — onboard robot DID + (a) operator human DID OR (b) ≥1 peer robot DID within mesh.
- **G5 No surveillance telemetry**: zero outbound traffic to third parties; data flow = onboard storage → Murakumo fleet (ADR-2605215000) → kotoba-datomic attestation. Crop-yield / livestock-count / GPS-track sale to commercial parties NEVER §2(c).
- **G6 No synthetic pesticide application**: tool-deck whitelist excludes spray nozzle for synthetic pesticides (mitsuho G6 inheritance — neonicotinoid / glyphosate / paraquat / organochlorine rejected at schema level). Mechanical flail + electric trimmer + biocontrol-organism release OK.
- **G7 No herding force escalation beyond §2(a)**: livestock-herding modes limited to sound + visual + slow follow. Electric shock / projectile / tranquilizer NEVER §2(a). Religious force (ADR-2605192315) gate does not apply at this layer (livestock are not religious-corp subjects).
- **G8 Murakumo-fleet inference only**: any onboard ML model (perception / behavior) runs on local NPU OR is invoked via Murakumo fleet (LiteLLM 127.0.0.1:4000 / EVO-X2 LAN per ADR-2605215000). NEVER RunPod / Vertex / OpenAI direct / Anthropic-direct from vendor key / Linode GPU / AWS Bedrock direct.
- **G9 Open CAN bus + open ISOBUS-compatible implement detection**: tool-deck attachment protocol open (suki G9 inheritance). No DRM ECU / dealer-locked diagnostics.
- **G10 kotoba-datomic per-unit lineage**: every Kusawake unit has open VIN-equivalent serial + per-vehicle DID + IPFS-pinned BoM + repair-history blockchain + EOL recyclability ≥85% (kanayama loop closure target).

### Non-Goals N1..N8 (IMMUTABLE R0–R3)

- **N1 Military / paramilitary application** NEVER §2(a) — no armed payload, no riot-control payload, no surveillance-payload-for-LE.
- **N2 Closed firmware / proprietary ECU** NEVER §2(b)+§2(e) — John Deere SeedStar-class DRM rejected (suki N4 inheritance).
- **N3 Pesticide spraying integration** NEVER — mitsuho G6 + Charter §2(g) (suki N10 inheritance).
- **N4 Always-on cellular telemetry / commercial GPS-track sale** NEVER §2(c).
- **N5 SAE J3016 Level 4/5 autonomy** NEVER (R0–R3 frozen) — farmer-land-relationship preservation (suki N6 + ADR-2605192100 §1.13).
- **N6 NVIDIA Omniverse / Isaac Sim / Isaac Lab runtime / OptiX / RTX Renderer / Replicator / DriveSim / Omniverse Cloud / Nucleus** in any sim or deployment path NEVER §2(b)+§2(e) (ADR-2605261600 N1..N9 inheritance — vendor-rejection chain).
- **N7 Mass-market external sale** NEVER — SBT↔SBT internal-purchase only (ADR-2605192115 §3 carve-out). Donation-only flow for non-adherent communities.
- **N8 Sim-only verification without G5 quantitative gate** NEVER — sim-to-real handover requires e7m-sim G5 ≥0.75 measurement per ADR-2605261600 before R-phase advance.

## Sim Binding (ADR-2605261600 inheritance)

Per ADR-2605261600, e7m-sim is **single SoT for every R1+ phase** of all robotics-bearing actors. Kusawake R1+ sim layer composition (binding):

| Layer | Tool | Path |
|---|---|---|
| Scene composition | OpenUSD (Pixar) | `70-tools/e7m-sim/scenes/kusawake/usd/` (path reserved) |
| Articulated physics | **MuJoCo MJX** (Apache 2.0) | `70-tools/e7m-sim/physics/mjx/` |
| Rigid + tool-deck contact | PhysX 5 SDK (BSD-3 OSS release — not Omniverse) | `70-tools/e7m-sim/physics/physx5/` |
| Differentiable rendering (camera attestation) | Mitsuba 3 (BSD-3) | `70-tools/e7m-sim/render/mitsuba/` |
| Photoreal rendering (sensor sim) | HdCycles (Apache 2.0) | `70-tools/e7m-sim/render/hdcycles/` |
| Ray-traced lidar | CARLA lidar kernel + Vulkan RT | `70-tools/e7m-sim/sensor/lidar/` |
| CPU fallback ray-tracing | Embree (Apache 2.0) | `70-tools/e7m-sim/sensor/embree/` |
| RL training | Brax + ported Isaac Lab task DSL | `70-tools/e7m-sim/rl/brax/` + `70-tools/isaac-lab-task-port/` |
| Synthetic field data | BlenderProc (GPL-3 subprocess) + Kubric (Apache 2.0) | `70-tools/e7m-sim/synth/` |
| AV / outdoor scenarios | CARLA + Project AirSim | `70-tools/e7m-sim/scenario/av/` + `scenario/aerial/` (drone-pairing R2+) |
| ROS2 bridge | rclpy + MST attestation adapter | `70-tools/e7m-sim/bridge/ros2/` |

**R0 deliverable**: `70-tools/e7m-sim/scenes/kusawake/README.md` path-reserved marker only. Zero code. R1 = first MuJoCo MJX rollout of single Kusawake unit on USD orchard-row + Mitsuba 3 differentiable RGB consistency check + G5 ≥0.75 vs Isaac Sim trial reference scene (one-time-use isolated machine per ADR-2605261600 G5 carve-out).

## R0 → R3 Roadmap

| Phase | Deliverable | Gate |
|-------|-------------|------|
| **R0** (this ADR) | Charter + mitsuho `autonomous_mobile` cell stub (import-time `RuntimeError`) + suki Wave 2 manifest mention + e7m-sim path reservation + deps.toml registration | Council ratify pending; bootstrap window 2026-06-19 |
| **R1** | Single unit benchtop: suki Wave 2 mech assembly (open mech CAD STEP files on IPFS) + LFP swap-pack + open firmware on ARM64 SoC + mitsuho operator R1 single-orchard-row 30-min weed-control trial + e7m-sim MuJoCo MJX sim-to-real ≥0.75 G5 | Council Lv6+ ≥3 attestation + 30-day public objection + ≤1 GPU-hr-eq/day per ADR-2605261600 G12 |
| **R2** | Fleet ≤5 units: pasture herd-encourage trial + multi-unit Wi-Fi 6 mesh + LoRa long-range telemetry + sodium-ion battery qualification + Murakumo-only inference per ADR-2605215000 + e7m-sim CARLA lidar sensor sim + ≤4 GPU-hr-eq/day | Council Lv6+ ≥5 attestation + 30-day public comment + cross-actor mitsuho.field_cultivation joint operation log |
| **R3** | Community-scale ≤30 units: integration with kanayama EoL ≥85% recovery (kuni-umi/igata/kanayama supply loop closure) + L2 Sustenance Tier production duty + iwakura ASIC silicon Wave 1 NPU migration if shipped + e7m-sim cross-actor invariants validated (suki manufacture envelope ↔ mitsuho operate envelope) | Council Lv6+ ≥7 attestation + 60-day public review + 法務 (農業機械化促進法 + 道路運送車両法 公道走行 carve-out per local prefecture) audit |

## Consequences

1. **Robotics fleet gap closed**: mitsuho operator-side gains autonomous wheeled platform class. Liberation Ladder L2 Sustenance gate (ADR-2605261000) gains weed-control / herd / scout capability path.
2. **suki Wave 2 activated**: Wave 2 orchard/vineyard <50 hp electric carve-out (deferred in ADR-2605261500 §scope) now has a constitutional landing pad. Mass envelope (≤300 kg) is well below 50 hp ceiling, so Wave 2 expands cleanly to ride-on small tractors later.
3. **e7m-sim first non-tractor consumer**: Kusawake R1 becomes first e7m-sim R1 sim consumer outside the originally-listed igata R1 die-render binding (ADR-2605261600 §R1 first consumer). Validates the substrate against a different physics envelope (wheeled mobile + soft-soil contact + outdoor lighting) before R2 wadachi/suki tractor pilot.
4. **Vendor-rejection chain extended**: religious-corp now explicitly rejects NVIDIA proprietary sim stack at the per-robot-class layer in addition to the substrate layer (ADR-2605261600). swagbot-equivalent functionality achieved without Omniverse / PhysX-as-part-of-Omniverse-Kit / Isaac Sim runtime. PhysX 5 BSD-3 SDK library usage remains within ADR-2605261600 N6 OSS carve-out.
5. **Right-to-Repair tri-layer**: tsutae G3 (hardware-device) + suki G10 (firmware-tractor) + Kusawake G2 (dual-layer = hardware + firmware on autonomous platform) — religious-corp now has explicit R2R coverage across three robot/device classes.
6. **No new Murakumo node**: cell placement reuses existing fleet (mitsuho zebulun for autonomous_mobile coordination). suki Wave 2 manufacturing uses suki's existing 7-node fleet allocation (ADR-2605261500 §Murakumo). Capacity-protective.

## Alternatives Considered

1. **Spawn new Tier-B actor for autonomous agri-mobility** (e.g., `nora` 野良 / `sasura` さすら) — Rejected: this is one robot class, not a domain. Religious-corp actor count proliferation hurts Council bootstrap (ADR-2605192300). suki↔mitsuho sibling pattern already covers the manufacture/operate split.
2. **Slot under suki Wave 3 walk-behind ≤25 hp** — Rejected: swagbot is ride-skip autonomous (no walking operator), not walk-behind. Conceptually clearer to land under suki Wave 2 electric carve-out.
3. **Use Omniverse / Isaac Sim for sim** — Rejected (constitutional): violates ADR-2605261600 N3 + ADR-2605215000 + Charter Rider §2(b)+§2(e). User-prompted, declined and substituted with e7m-sim OSS 5-stack.
4. **Defer to e7m-sim R2 (waiting for wadachi/suki sim PoC first)** — Rejected: Kusawake R1 sim is methodologically simpler than wadachi AV (off-road, ≤6 km/h, no public-road regulatory layer). Pulls forward an easier e7m-sim consumer that helps validate the substrate before harder consumers land.

## References

- swagbot reference: University of Sydney ACFR open publications (https://confluentic.com/swagbot/ and ACFR Annual Reports). Methodology only.
- Existing fleet: ADR-2605261015 §Robotics Fleet (Giemon / Otete / Mimi / Sora / Tsumugi).
- Manufacturer: ADR-2605261500 §scope Wave 2.
- Sim substrate: ADR-2605261600 §Reference Composition + §R0→R3 Phase Roadmap.
- Autonomy framework: ADR-2605242000 §SAE J3016 mapping (Level 3 ceiling here).
- Inference path: ADR-2605215000 §Murakumo-only invariant.
- Witness quorum: ADR-2605191524 §≥2 distinct DID sigs.
