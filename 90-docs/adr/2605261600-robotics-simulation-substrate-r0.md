---
id: adr-2605261600-robotics-simulation-substrate-r0
title: Robotics Simulation Substrate R0 Charter — OSS USD+Hydra+MuJoCo MJX+Embree+BlenderProc 5-stack reference; Omniverse / Isaac Sim / OptiX / RTX Renderer / Replicator structurally rejected
status: proposed
doc_type: adr
topic: robotics/simulation/substrate
authoritative: true
last_verified: 2026-05-26T00:00:00Z
related:
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605250500-yakushi-pharmaceutical-rd-charter
  - 2605250715-tatekata-construction-tier-b-actor-r0.md
  - adr-2605252200-watatsumi-civilian-submersible-r0
  - adr-2605252400-kanayama-circular-metallurgy-r0
  - adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
  - adr-2605261015
  - adr-2605261115-makura-foam-pillow-tier-b-actor-r0
  - adr-2605261115-igata-megacasting-tier-b-actor-r0
  - adr-2605261215-igata-r1-benchtop-commissioning
  - adr-2605261300-tsutae-handheld-communication-tier-b-actor-r0
  - adr-2605261330-futawa-motorcycle-tier-b-actor-r0
  - adr-2605261500-suki-farm-tractor-tier-b-actor-r0
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
depends_on:
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
---

# ADR-2605261600: Robotics Simulation Substrate R0 Charter

**Date**: 2026-05-26
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Master charter establishing the religious-corp **first-party robotics simulation substrate** as a single SoT for every R1+ benchtop / R2+ pilot / R3+ community-scale phase of every robotics-bearing Tier-B actor (wadachi / suki / igata / watatsumi / sarutahiko / futawa / tatekata / kuni-umi / hodoki / silicon Wave 1+2 robotics fleet).

## Context

religious-corp currently has **zero** robotics simulation integration. Audit (2026-05-26):

- Repo-wide grep of `omniverse` / `isaac.?sim` / `optix` / `physx` / NVIDIA-`hydra` (USD) → **0 hits** (the only `optix` match is an accidental substring inside `package-lock.json` integrity hash).
- Repo-wide grep of other robotics simulators (Gazebo / MuJoCo / Drake / Webots / PyBullet / CoppeliaSim / CARLA / AWSIM) → **0 hits**.
- All robotics-bearing actor (wadachi / suki / igata / watatsumi / sarutahiko / futawa / tatekata / kuni-umi / hodoki / makura / tsutae) are R0 scaffolds — every Pregel cell `.solve()` raises import-time RuntimeError. Robot classes (Otete / Mimi / Hitogata / Kasane / Tsugite / Kuwa / Norikata / Hibachi / Tatara / Watari / Awa / Hagasu / Nuku / Tokike / Sango / Tako / Hibiki / Ama / Norimichi / Migaki / Yokin / Kamado / Tedama / Tezukai / Tsutsumi / Akari / Norikata / Sukoyaka / Yutori / Hizukue / Tsumugi / Funamori / Sora / Hoshi / Quad / Giemon) are **class reservations only**; firmware / PoC is R1+ work.
- Real-machine verification path is currently defined as **kotoba-datomic Ed25519 witness quorum + IPFS-pinned photographs** (ADR-2605231400 §4 membrane + ADR-2605231902 first projection precedent); no 3D / physics / sensor sim layer is specified.

This means every R1 ADR (yakushi R1 ADR-2605250630 / igata R1 ADR-2605261215 / mitate R1 ADR-2605260200) currently has to **invent its own sim story from scratch** when commissioning benchtop hardware. Each R1 author independently faces:

1. Which 3D scene description format (URDF / MJCF / OpenUSD / SDF)?
2. Which physics engine (rigid + articulated + soft + fluid)?
3. Which renderer (rasterizer / path tracer / hybrid)?
4. Which sensor simulator (camera RGB-D / lidar / radar / IMU / contact / force-torque)?
5. Which RL / planning training pipeline?
6. Which synthetic-data / domain-randomization tool?
7. How does sim output get attested back to kotoba-datomic?

Without a single canonical substrate, each Tier-B actor will land an ad-hoc combination, drift will compound, and the **cross-actor simulation invariants** (e.g., sarutahiko-truck physics must agree with wadachi-operator physics for the same vehicle; suki-tractor sim must agree with mitsuho.harvest_robotics operation envelope) will silently diverge.

### Industry reference: NVIDIA Omniverse + Isaac Sim + Isaac Lab

The de-facto industry reference for end-to-end robotics simulation as of 2026-05 is the **NVIDIA Omniverse stack**:

- **Omniverse Kit** — USD-native authoring + collaboration platform
- **Isaac Sim** — robotics sim runtime on top of Omniverse Kit
- **Isaac Lab** — RL / sim-to-real training infrastructure on top of Isaac Sim
- **RTX Renderer** — OptiX-backed path-tracing renderer for photoreal sensor sim
- **PhysX 5** — rigid body + articulated + soft body + cloth + fluid physics
- **Replicator** — synthetic-data generation pipeline with domain randomization

Honest scoring (10 dimensions, OSS-combo vs Isaac Sim/Lab; rationale tracked in `90-docs/baien/sim-substrate-scoring-260526.md`):

| Dimension | OSS combo (USD+HdCycles+MuJoCo MJX+Embree+BlenderProc) | Isaac Sim/Lab |
|---|---|---|
| Scene composition (OpenUSD) | 9 | 10 |
| **Photoreal rendering (path tracing)** | **4-5** | **10** (RTX Renderer / OptiX) |
| **Ray-traced sensor sim (RTX-Lidar)** | **2** | **10** |
| Rigid + articulated physics | 9 (MuJoCo MJX) | 8 |
| Soft body / cloth / fluid | 4 | 8 (FleX / PhysX 5) |
| GPU-parallel RL envs | 7 (Brax / MJX / Genesis) | 10 (Isaac Lab) |
| Sensor zoo | 5 | 9 |
| **Asset library (SimReady warehouse / robots)** | **3** | **9** |
| **Synthetic-data pipeline (Replicator)** | **5** | **9** |
| ROS2 bridge | 7 | 9 |
| **Aggregate** | **~60-65 / 100** | **~88 / 100** |

The four largest gaps (rendering / sensor sim / asset library / synthetic data) are **engineering-investment-bounded, not architecture-bounded** — they can be closed by composing existing OSS pieces and by spending curation budget on the asset library.

### Why this cannot collapse into "just use Omniverse / Isaac Sim"

Adopting the Omniverse stack as-is would violate **multiple constitutional invariants simultaneously**:

| Constraint | Violated by |
|---|---|
| §2(b) anti-secrecy (ADR-2605192100 + ADR-2605192200) | Omniverse Kit + Isaac Sim runtime + OptiX (closed-source EULA) |
| §2(e) anti-gatekeeping | Vendor lock-in to NVIDIA + Omniverse account binding + Nucleus collaboration server |
| ADR-2605215000 no-commercial-GPU-rental | Omniverse Cloud (NVIDIA-hosted GPU rental for collaborative authoring + rendering) |
| CHARTER-RIDER §2(b) NOTICE preservation | Closed-source binaries cannot carry the Charter Rider notice in source form |
| §2(e) data-sovereignty | Replicator synthetic-data pipelines depend on Nucleus collaboration server |
| ADR-2605215000 inference SSoT (Murakumo only) | Isaac Lab assumes NVIDIA driver + CUDA + closed BSP; cannot run on Murakumo Mac mini fleet |

A constitutional "use Omniverse only for sim, not for shipped firmware" carve-out is **not viable** because:

1. The output of sim (URDF revisions / RL policy weights / synthetic datasets / behavior trees) flows directly into shipped firmware. If the sim runtime is closed, the firmware provenance chain is broken at the sim layer, which means `kotoba-datomic attestation lineage` cannot be verified end-to-end (this would violate ADR-2605231400 §4 membrane structurally — auditors cannot reproduce the sim that produced the policy).
2. §2(b) anti-secrecy applies to the **substrate of decision-making**, not only to the shipped artifact. Closed sim = closed substrate.
3. Omniverse Cloud is unavoidable in practice once a team adopts Omniverse Kit (collaborative authoring + Nucleus + asset publish) — even if technically possible to self-host all of it, the recommended-path UX herds users into NVIDIA-hosted services.

### Why this cannot collapse into "just use MuJoCo / Drake / Genesis alone"

Each single-tool path has structural gaps that the religious-corp robotics fleet hits:

- **MuJoCo alone** → no photoreal rendering, no ray-traced lidar (wadachi AV sim impossible; watatsumi lidar bathymetry impossible).
- **Drake alone** → planning-grade, but no GPU-parallel RL envs at fleet scale, no sensor zoo.
- **Genesis alone** → promising unified GPU stack but immature (no production-tested AV sensor sim, sparse ROS2 bridge as of 2026-05).
- **Gazebo / ROS2-sim alone** → mature ROS2 bridge but weak path-tracing, weak GPU-parallel RL.

The religious-corp robotics fleet needs all of: rigid + articulated + soft + sensor + RL + ROS2 + synthetic data + multi-actor cross-validation. **No single OSS tool covers this**; a composed substrate is required.

## Proposal

religious-corp adopts a **first-party robotics simulation substrate** anchored by a 5-stack OSS reference composition, with quantitative quality gates measured against NVIDIA Isaac Sim ground truth as a calibration anchor only (the anchor is calibration scaffolding, not a runtime dependency).

- **Substrate name**: `e7m-sim` (etzhayyim-sim; placeholder — final name confirmed at ratification)
- **Substrate path**: `70-tools/e7m-sim/` (mirrors `70-tools/e7m-dataset/` pattern from ADR-2605241500)
- **Isaac Lab task DSL port path**: `70-tools/isaac-lab-task-port/` (Apache-2.0 task definition headers only; runtime separated)
- **Scoring evidence path**: `90-docs/baien/sim-substrate-scoring-260526.md` (R0 scaffold; per-dimension methodology + per-actor pilot run logs land here R1+)
- **Bindings (R1 single SoT)**: wadachi R1 / suki R1 / igata R1 / watatsumi R1 / sarutahiko R1 / futawa R1 / tatekata R1 / hodoki R1 / makura R1 / tsutae R1 sim layers MUST use this substrate; deviation requires a per-actor sim ADR + Council Lv6+ ≥3 attestation.
- **Cross-actor invariants** (suki↔mitsuho operation envelope agreement / sarutahiko↔wadachi vehicle physics agreement / igata↔wadachi/tatekata/watatsumi structural-part finite-element agreement) are computed in this substrate (no separate "cross-actor CAE tool" carve-out).
- **R0 deliverable**: this charter ADR + reserved scaffold path + Isaac Lab task DSL port path + scoring evidence skeleton. NO code, NO Pregel cells, NO lexicons land at R0. R1 = renderer differential PoC; R2 = sensor sim + 1 actor pilot; R3 = cross-actor validation harness.

## Constitutional Gates (G1..G14, IMMUTABLE R0..R3)

**G1 Open architecture invariant**: every layer of the substrate (scene composition / render delegate / physics / sensor sim / RL training / synthetic data / ROS bridge / asset import) MUST be OSS license compatible with Apache 2.0 + Charter Rider §2 (Apache 2.0 / BSD-2 / BSD-3 / MIT / MPL 2.0 / Pixar Animation Studios USD License acceptable; GPL-3 acceptable for tool-level dependencies via subprocess invocation only — never linked into shipped firmware to preserve Charter Rider §4 distribution rules).

**G2 OpenUSD as the single scene-composition SoT**: scene description is Pixar OpenUSD; URDF / MJCF / SDF are accepted as import formats but normalized to USD on intake. No proprietary scene format (NVIDIA-extended USD `omni.*` schemas, Unity prefab, Unreal `.umap`) at any layer.

**G3 Vulkan Ray Tracing as the GPU-neutral ray-tracing backbone**: GPU ray tracing (for sensor sim and photoreal rendering) uses **Vulkan Ray Tracing** (Khronos open standard, runs on NVIDIA RTX + AMD RDNA2+ + Intel Arc). OptiX (closed) is N1 NEVER. CPU fallback path uses Embree (Apache 2.0 / Intel) so that the substrate runs end-to-end on Murakumo Mac mini fleet without discrete GPU.

**G4 Murakumo-fleet-only execution (ADR-2605215000 strict inheritance)**: substrate runtime MUST run on the Murakumo fleet (LiteLLM 127.0.0.1:4000 + EVO-X2 LAN 192.168.1.70 + Mac mini Ollama). Cloud GPU rental (Omniverse Cloud / Lambda Labs / RunPod / Vertex AI / AWS Bedrock GPU / Anthropic-direct GPU paths / Linode GPU / any third-party hosted GPU) is N2 NEVER. religious-corp owned discrete GPU (W7900 / future MI-class / iwakura ASIC silicon Wave 1) acquisition is the only escalation path beyond the current Mac mini + EVO-X2 capacity.

**G5 Quantitative quality gate against Isaac Sim ground truth ≥ 0.75**: for every R1+ actor, the substrate output MUST score ≥ 0.75 versus an Isaac Sim-generated reference scene on at least the four following metrics per applicable modality:

- **Rendering**: PSNR ≥ 25 dB (vs Isaac Sim RTX Renderer reference at same camera pose, same materials, same lighting) AND SSIM ≥ 0.85
- **Lidar**: Chamfer distance ≤ 0.05 m (between substrate-generated point cloud and Isaac Sim RTX-Lidar reference at same scene) AND point-cloud IoU ≥ 0.75 at 0.10 m voxelization
- **Physics**: end-effector trajectory L2 deviation ≤ 5% across 100 standardized articulated-arm reach trials (substrate vs Isaac Sim PhysX 5 reference)
- **Sim-to-real**: real-world rollout success rate ≥ 0.75 × substrate-sim rollout success rate on the same task (measured at R2 actor pilot using actual robot hardware)

Each metric has a per-actor variance budget ratified at the actor's R1 ADR. **Below 0.75 = R1 ADR is REJECTED.** The Isaac Sim reference scene is generated only once per actor (on a one-time-use Isaac Sim trial license + isolated machine outside the religious-corp infrastructure; **never integrated into the religious-corp runtime**, never connected to Murakumo / Nucleus / Omniverse Cloud, never carries religious-corp keys). After scoring, the Isaac Sim reference scene is archived as a sealed CID on kotoba-datomic and the trial machine is decommissioned.

**G6 kotoba-datomic attestation lineage MANDATORY for every sim run**: every simulation run MUST emit a `simulationRunAttestation` lexicon record with `{sceneCid, physicsConfigCid, rendererConfigCid, sensorConfigCid, seedSequence, witnessQuorum[≥2 substrate-instances], gpuFingerprintCid, durationSec, outputArtifactCids[]}` so that any downstream firmware artifact (URDF revision / RL policy weights / synthetic dataset) is structurally chained back to the sim runs that produced it. Sim that does not attest is unusable for downstream Pregel cell consumption (cell `.solve()` raises `RuntimeError` on un-attested input).

**G7 Reproducibility invariant — deterministic seed + bit-identical replay**: every sim run is reproducible bit-identical given `{sceneCid, physicsConfigCid, rendererConfigCid, sensorConfigCid, seedSequence}` on identical hardware. Cross-hardware reproducibility allows numerical noise ≤ 1e-4 L2 per step (documented in `90-docs/baien/sim-substrate-reproducibility-260526.md` R1+). This is the analogue of ADR-2605242630 R1a `dispatchLoraForward` numerical-path discipline applied to sim.

**G8 No NVIDIA-account-required tool in the substrate runtime**: tools that require NVIDIA developer account / Omniverse account / NVIDIA NGC API key at runtime are N3 NEVER. Build-time download of OSS PhysX 5 BSD-3 source from a public mirror (GitHub release, not NVIDIA NGC) is acceptable.

**G9 No proprietary plugin in the substrate runtime**: closed-source plugins (NVIDIA Isaac Sim plugins, Unity Editor plugins, Unreal Engine plugins, MuJoCo-Pro pre-2022 closed plugins) are N4 NEVER. PhysX 5 SDK (BSD-3 since 2018-2022) is acceptable as a library because its source is open; bundled NVIDIA cooking-cache binaries are NOT loaded (cooking happens at runtime from open source on every Murakumo node).

**G10 Charter Rider §2 scan applied to every imported asset**: every imported 3D asset (mesh / texture / material / animation / behavior tree) MUST pass `etzhayyim_organism.sensors.charter_rider.scan()` (per ADR-2605192200 + baien tooling index). Failed scans REJECT the asset; reviewer-gated override requires Council Lv6+ ≥3 attestation. This blocks military / weapons / surveillance / addiction-design / eschatology imagery from entering the religious-corp asset library through 3D-asset-marketplace import paths.

**G11 Personnel vetting for sim-to-real handover**: any human operator who transfers a sim-validated firmware artifact to a real robot MUST be Adherent SBT holder + actor-specific R-phase SME (e.g., HPDC operator for igata R1 sim-to-real, ag-mechanic for suki R1 sim-to-real, ag-machine operator for mitsuho sim-to-real). Sim handover lineage MUST emit `simToRealHandoverAttestation` lexicon record signed by the SBT operator's DID.

**G12 KPI caps on substrate runtime resource consumption**: at R1, substrate runs ≤ 1 GPU-hour-equivalent per actor per day (Murakumo capacity-protective). R2 ≤ 4 GPU-hour-equivalent / actor / day. R3 ≤ 16 GPU-hour-equivalent / actor / day. Substrate runs that exceed the cap are queued and warned; Council Lv6+ supermajority can raise per-actor cap on a per-quarter basis. This protects Murakumo fleet inference capacity (ADR-2605215000) from being starved by sim workloads.

**G13 No telemetry / no usage analytics / no crash reporting to third parties**: the substrate emits zero outbound network traffic except to Murakumo fleet endpoints and kotoba-datomic attestation endpoints. NVIDIA telemetry / Khronos telemetry / Mesa telemetry / Blender Cycles telemetry / any "anonymous usage statistics" MUST be compile-time disabled at build. §2(c) anti-surveillance applied to the development tooling itself.

**G14 30-year reproducibility commitment**: the substrate MUST be reproducible-from-source for 30 years post-release per actor R1 ADR. Source pins (git SHAs, IPFS CIDs of release tarballs, build container manifest CIDs) are sealed on kotoba-datomic at every R-phase activation. Closed-source tools cannot satisfy this gate (vendor EULA can revoke access; CUDA versions deprecate; OptiX versions become unsupported). §2(b) anti-secrecy + §1.13 Wellbecoming applied to engineering substrate longevity.

## Non-Goals (N1..N10, IMMUTABLE R0..R3)

**N1 NVIDIA OptiX (closed)** at any tier ever — §2(b) anti-secrecy violation; Vulkan Ray Tracing (G3) is the structural replacement.

**N2 Commercial GPU rental** (Omniverse Cloud / Lambda Labs / RunPod / Vertex AI GPU / AWS Bedrock GPU / Anthropic-direct GPU / Linode GPU / any third-party hosted GPU) — direct ADR-2605215000 violation; Murakumo fleet (G4) is the structural replacement. R3+ religious-corp owned discrete GPU + iwakura ASIC (silicon Wave 1) are the only escalation paths.

**N3 NVIDIA Omniverse Kit / Isaac Sim runtime / Isaac Lab runtime / RTX Renderer / Replicator** as a runtime dependency at any tier — proprietary EULA + closed-source + NVIDIA-account-required + Nucleus collaboration server lock-in violates §2(b) + §2(e) + G6 + G8 simultaneously. **Carve-out (sole exception)**: Isaac Sim trial license usage to generate G5 ground-truth reference scenes on a one-time-use isolated machine (described in G5) — never connected to religious-corp infrastructure, never carrying religious-corp keys, archived as sealed CID, machine decommissioned. **Carve-out (sole exception)**: Isaac Lab Apache-2.0 task definition DSL headers may be ported to `70-tools/isaac-lab-task-port/` for task-definition compatibility; the Isaac Lab runtime itself is N3 NEVER.

**N4 NVIDIA DriveSim** (proprietary AV simulator) — §2(b) + §2(c) violation; OSS AV sim alternatives (CARLA MIT + AWSIM Apache 2.0 + Project AirSim Apache 2.0 + MetaDrive Apache 2.0) are the structural replacement for wadachi R2+ AV scenario sim.

**N5 Unity (closed) / Unreal Engine (closed source for commercial)** as a substrate component — §2(b) violation. Unity Apache-licensed packages individually may be considered on a case-by-case Council vote (e.g., Unity Robotics Hub URDF importer Apache 2.0); the Unity Editor itself is N5 NEVER.

**N6 Closed-source physics engines** (Havok / proprietary FleX bundles / proprietary destructibles) — §2(b) violation. PhysX 5 SDK (BSD-3) is the only acceptable PhysX-family component; NVIDIA cooking-cache binaries are excluded (G9).

**N7 Third-party cloud-based asset marketplaces** (NVIDIA SimReady asset library hosted on Omniverse Cloud / Sketchfab as a runtime dependency / TurboSquid as a runtime dependency) — §2(c) anti-surveillance + §2(e) anti-gatekeeping. Assets MAY be one-time-downloaded from CC-BY / CC0 / Apache 2.0 sources, scanned per G10, and pinned to IPFS as religious-corp asset library; runtime fetch from marketplace APIs is N7 NEVER.

**N8 Third-party-cloud collaborative authoring** (Omniverse Nucleus / Foundry Nuke Studio Cloud / Autodesk cloud) — §2(c) + G13 violation. Collaborative USD authoring is restricted to git + IPFS + Murakumo fleet hosting only.

**N9 Closed-source synthetic-data services** (Replicator / Parallel Domain / AI.Reverie) — §2(b) + §2(e) violation. BlenderProc (GPL-3 subprocess invocation) + Kubric (Apache 2.0) are the structural replacement (G1 subprocess-invocation carve-out for GPL).

**N10 Telemetry / crash-reporting / usage-analytics to any third party** (NVIDIA / Khronos / Mesa / Blender Foundation / etc.) — §2(c) violation; G13 enforces. Compile-time disable required.

## Reference Composition (Wave 1 — single fixed reference for R1 bindings)

The following 5-stack composition is fixed at R0 and binding for all actor R1 ADRs:

| Layer | Wave 1 Reference | License | Substrate path |
|---|---|---|---|
| Scene composition | **OpenUSD (Pixar)** | Pixar Animation Studios USD License (Apache-2.0-compatible) | `70-tools/e7m-sim/usd/` |
| Render delegate (photoreal) | **HdCycles** (Blender Cycles via Hydra delegate) | Apache 2.0 | `70-tools/e7m-sim/render/hdcycles/` |
| Render delegate (differentiable) | **Mitsuba 3** | BSD-3 | `70-tools/e7m-sim/render/mitsuba/` |
| Ray-traced sensor backbone (GPU) | **Vulkan Ray Tracing** + open shader library | Khronos open standard | `70-tools/e7m-sim/sensor/vulkan-rt/` |
| Ray-traced sensor backbone (CPU fallback) | **Embree** | Apache 2.0 | `70-tools/e7m-sim/sensor/embree/` |
| Lidar sim | **CARLA lidar kernel** + Vulkan RT custom delegate | MIT + Khronos | `70-tools/e7m-sim/sensor/lidar/` |
| Physics (articulated, GPU-parallel) | **MuJoCo MJX** | Apache 2.0 | `70-tools/e7m-sim/physics/mjx/` |
| Physics (rigid + destruction) | **PhysX 5 SDK** | BSD-3 | `70-tools/e7m-sim/physics/physx5/` |
| Physics (unified GPU experimental) | **Genesis** | Apache 2.0 | `70-tools/e7m-sim/physics/genesis/` |
| Multibody dynamics + planning | **Drake** | BSD-3 | `70-tools/e7m-sim/planning/drake/` |
| RL training | **Brax** + ported Isaac Lab task DSL | Apache 2.0 + Apache 2.0 (port) | `70-tools/e7m-sim/rl/brax/` + `70-tools/isaac-lab-task-port/` |
| Synthetic data | **BlenderProc** (subprocess) + **Kubric** | GPL-3 (subprocess only, G1 carve-out) + Apache 2.0 | `70-tools/e7m-sim/synth/blenderproc/` + `70-tools/e7m-sim/synth/kubric/` |
| Indoor asset library | **Habitat-Matterport 3D** + **ProcTHOR** + **RoboCasa** | CC-BY + Apache 2.0 + MIT | `70-tools/e7m-sim/assets/indoor/` (G10 scan + IPFS pin) |
| AV scenario (wadachi R2+) | **CARLA** + **AWSIM** (Autoware-native USD) | MIT + Apache 2.0 | `70-tools/e7m-sim/scenario/av/` |
| Drone / aerial (sora / Hoshi) | **Project AirSim** (Apache 2.0 successor) | Apache 2.0 | `70-tools/e7m-sim/scenario/aerial/` |
| ROS2 bridge | **rclpy** + custom MST attestation adapter | Apache 2.0 | `70-tools/e7m-sim/bridge/ros2/` |
| Multi-GPU + multi-node orchestration | **Ray** + Murakumo fleet placement | Apache 2.0 | `70-tools/e7m-sim/orchestration/ray/` |

**Three non-symmetric advantages over Isaac Sim/Lab** (the substrate intentionally optimizes for these):

1. **MuJoCo MJX articulated contact accuracy** — legged-locomotion / dexterous-manipulation sim-to-real research-SOTA (Boston Dynamics / DeepMind / OpenAI Hand). Materially better than PhysX for high-contact articulated systems.
2. **Mitsuba 3 differentiable rendering** — inverse rendering / scene identification / "is the camera attestation consistent with the scene?" verification path. Not present in Omniverse stack.
3. **Vulkan Ray Tracing GPU-vendor neutrality** — substrate runs on AMD MI-class GPU + Intel Arc + iwakura ASIC (silicon Wave 1 ADR-2605242500) without CUDA / OptiX lock-in. Future religious-corp owned GPU acquisitions are not blocked by NVIDIA SKU availability.

## R0..R3 Phase Roadmap

**R0 (this ADR — scaffold only)**:
- This charter ADR landed
- Scaffold paths reserved: `70-tools/e7m-sim/` + `70-tools/isaac-lab-task-port/` + `90-docs/baien/sim-substrate-scoring-260526.md`
- Zero code, zero Pregel cells, zero lexicons
- Council Lv6+ ≥3 attestation REQUIRED to advance to R1

**R1 (renderer differential PoC — `e7m-sim` Wave 1 minimum viable)**:
- HdCycles render delegate wired to OpenUSD via Hydra
- Mitsuba 3 differentiable rendering PoC on a single scene
- Embree CPU fallback path verified on Murakumo Mac mini
- Single test scene (Stanford bunny + Cornell box) renders bit-identically deterministic (G7) on 3 of 10 Murakumo nodes
- G5 rendering quality gate measured against one-time Isaac Sim RTX Renderer reference scene: PSNR ≥ 25 dB, SSIM ≥ 0.85
- Council Lv6+ ≥3 attestation per actor first sim layer; first eligible actor = igata R1 (ADR-2605261215) static die surface render (low scene complexity, no sensor sim)
- `simulationRunAttestation` lexicon scaffolded; first attestation lands

**R2 (sensor sim + 1 actor pilot)**:
- Vulkan Ray Tracing GPU path on EVO-X2 functional
- Lidar sim (CARLA lidar kernel) wired to Vulkan RT delegate
- MuJoCo MJX articulated physics PoC on a single 6-DoF arm (likely Otete-class)
- First actor pilot = **wadachi R1 → R2 transition** (single intersection AV scenario in CARLA) OR **suki R1 → R2 transition** (single tractor in field harvest scenario via MJX)
- G5 lidar quality gate measured: Chamfer distance ≤ 0.05 m vs Isaac Sim RTX-Lidar reference
- G5 physics quality gate measured: end-effector trajectory L2 ≤ 5% vs PhysX 5 reference (PhysX 5 BSD-3 used standalone; Isaac Sim runtime not invoked)
- Synthetic data pipeline (BlenderProc subprocess) emits first domain-randomized dataset for an actor; CID pinned to IPFS; Charter Rider G10 scan passes
- 30-day public comment window opened
- Council Lv6+ ≥3 attestation per actor R2 sim wiring

**R3 (cross-actor validation harness + community-scale)**:
- All robotics-bearing Tier-B actors R1+ migrated to substrate
- Cross-actor invariants live-validated:
  - sarutahiko-truck physics ↔ wadachi-operator physics agreement (same vehicle, two actor scaffolds)
  - suki-tractor sim ↔ mitsuho.harvest_robotics operation envelope agreement
  - igata-cast structural part ↔ wadachi / tatekata / watatsumi finite-element consumer
- G5 sim-to-real gate measured at R3: real-world rollout success rate ≥ 0.75 × substrate-sim rollout success rate per actor
- Isaac Lab task DSL port at `70-tools/isaac-lab-task-port/` reaches feature parity for the task categories actually used by religious-corp actors
- 60-day public review window
- Murakumo fleet sim-capacity audit lands; if iwakura ASIC silicon Wave 1 R3 has shipped, sim workloads migrate off Mac mini fleet to ASIC capacity (relieves G12 caps)

## Bindings (R1 single SoT)

The following Tier-B actor R1 ADRs are STRUCTURALLY BOUND to this substrate at R1 ratification; sim-layer deviation requires a per-actor sim ADR + Council Lv6+ ≥3 attestation citing this charter:

| Actor R1 ADR | First sim use-case | Substrate components used at R1 |
|---|---|---|
| wadachi R1 (future ADR) | intra-site ≤1 m/s navigation | MuJoCo MJX + HdCycles + (R2+) CARLA |
| sarutahiko R1 (future ADR) | road-test rollout single-vehicle | MuJoCo MJX + HdCycles + (R2+) CARLA |
| suki R1 (future ADR-2605261515) | field-test ≤50 hp prototype | MuJoCo MJX + HdCycles |
| igata R1 (ADR-2605261215) | die surface thermal-stress visualization | HdCycles + Drake static analysis |
| watatsumi R1 (future ADR) | benchtop pressure-vessel ≤500 mm Ø + ≤30 m pool | MuJoCo MJX + Mitsuba 3 (underwater inverse rendering) |
| futawa R1 (future ADR-2605261345) | single-motorcycle prototype dyno + ABS calibration | MuJoCo MJX + HdCycles |
| tatekata R1 (future ADR-2605250730) | benchtop 0.5m×0.5m structural assembly | MuJoCo MJX + Drake |
| hodoki R1 (future ADR) | single-vehicle hand-disassembly + data-wipe demo | MuJoCo MJX |
| makura R1 (future ADR-2605261130) | benchtop ≤1 kg foam batch + 10-pillow lot | MuJoCo MJX (cloth + soft body) |
| tsutae R1 (future ADR-2605261315) | single-device PoC build (SMT + chassis + display) | MuJoCo MJX (precision pick-place) |

## Consequences

### Positive

1. **Eliminates per-R1-ADR sim story re-invention** — all R1 actor authors point to this charter rather than redesigning the sim stack each time.
2. **Cross-actor sim invariants become physically computable** — sarutahiko-truck physics and wadachi-operator physics are guaranteed-comparable because they run on the same MJX backend with the same `simulationRunAttestation` lineage.
3. **Vendor-rejection chain extends to robotics simulation** — religious-corp now has constitutional rejection of NVIDIA proprietary sim stack (Omniverse / Isaac Sim / OptiX / DriveSim / Replicator) added to its existing rejection chain (silicon Wave 1 vs NVIDIA GPU + yakushi vs branded OTC + watatsumi vs naval defense + kanayama vs primary mining + igata vs IDRA giga press lock-in + tsutae vs Snapdragon/Apple A + futawa vs Samsung Knox + suki vs John Deere DRM).
4. **Engineering-substrate longevity gate (G14 30-year reproducibility)** is now a constitutional invariant for sim — closed-source tools structurally fail this gate, so the substrate is forced toward OSS as a side-effect of §1.13 Wellbecoming + §2(b) anti-secrecy applied to engineering tooling.
5. **Murakumo capacity protection via G12 caps** — sim workloads cannot starve Murakumo fleet inference (ADR-2605215000 SSoT) without an explicit per-quarter Council vote.
6. **iwakura ASIC (silicon Wave 1) future migration path is clear** — G3 Vulkan RT GPU-neutrality means iwakura R3 can absorb sim workloads without a stack rewrite.
7. **First sim charter that explicitly scores against Isaac Sim ground truth (G5 ≥ 0.75 quantitative gate)** — quality is not a hand-wave; it is measured at each R1 ratification.

### Negative

1. **Substrate effort is significant** — 5-stack composition + Vulkan RT custom delegate + ROS2 bridge + asset curation + cross-actor invariant validation is multi-year work even with good OSS foundations.
2. **Quality gap of ~15-25 points vs Isaac Sim** (60-65 vs ~88 honest score) at R1 reference; expected to close to ~10 points at R2 (after Vulkan RT sensor sim lands) and ~5 points at R3 (after cross-actor validation harness lands + curated asset library matures).
3. **Asset library scarcity** — NVIDIA SimReady has ~10 years of curated asset investment; the religious-corp library starts at near-zero. R2+ asset import + Charter Rider scan + IPFS pinning workflow is the long-tail cost.
4. **R1-blocking dependency** — wadachi R1, suki R1, igata R1 future R1 ADRs are now structurally blocked on this charter reaching R1 (renderer differential PoC). If this substrate slips, actor R1 ratifications slip.
5. **Mac mini fleet sim capacity is limited** — G12 caps will bind quickly; iwakura ASIC silicon Wave 1 R3 is on the critical path for fleet-scale sim throughput.

### Risk: GPL-3 BlenderProc subprocess invocation

BlenderProc (GPL-3) is invoked via subprocess only and its outputs (synthetic datasets) are data products, not derived software works, so the GPL-3 contagion does not propagate into religious-corp Apache 2.0 + Charter Rider firmware. G1 explicitly documents this carve-out. If the FSF interpretation of "derivative work" tightens in future case law and BlenderProc subprocess invocation becomes infeasible, Kubric (Apache 2.0) is the fallback (lower quality but license-clean).

### Risk: PhysX 5 BSD-3 long-term maintenance

NVIDIA's commitment to maintaining PhysX 5 SDK under BSD-3 is voluntary. If NVIDIA retracts the BSD-3 release in some future version, religious-corp pins to the last BSD-3 commit SHA, vendors the source under `vendor/physx5-bsd3-pinned-<sha>/`, and PhysX 5 contributes to G14 30-year reproducibility from the pinned source. MuJoCo MJX (Apache 2.0, DeepMind) is the fallback for rigid-body physics if PhysX 5 BSD-3 becomes infeasible.

### Risk: Vulkan RT driver maturity on AMD / Intel

NVIDIA RTX has the most mature Vulkan RT path as of 2026-05; AMD RDNA2+ + Intel Arc are catching up. R1 PoC starts on NVIDIA-RTX-equipped EVO-X2 (Vulkan RT, not OptiX) and validates the same shaders on AMD RDNA3 + Intel Arc once religious-corp acquires those SKUs. If AMD / Intel Vulkan RT drivers prove infeasible for production sensor sim at R2, the substrate temporarily falls back to Embree CPU path (slower but vendor-neutral) until AMD / Intel driver maturity arrives.

## Alternatives Considered

### Alternative A — adopt NVIDIA Omniverse + Isaac Sim + Isaac Lab as-is (REJECTED)

Quality is the highest available (~88/100). REJECTED for constitutional reasons (§2(b) anti-secrecy + §2(e) anti-gatekeeping + ADR-2605215000 no commercial GPU rental + G14 30-year reproducibility infeasible under vendor EULA). Documented in Context §"Why this cannot collapse into 'just use Omniverse / Isaac Sim'".

### Alternative B — adopt MuJoCo MJX alone (REJECTED)

Highest-quality OSS physics; insufficient for AV sensor sim (wadachi), underwater lidar (watatsumi), photoreal rendering (any actor needing visual ML perception). REJECTED for coverage.

### Alternative C — adopt Genesis (Apache 2.0, unified GPU stack) as the single substrate (DEFERRED)

Promising unified differentiable physics + rendering, very new (2024 release). REJECTED for R1 reference because immaturity for production AV sensor sim and sparse ROS2 bridge as of 2026-05. Genesis is included as `e7m-sim/physics/genesis/` in the Wave 1 composition as an experimental component, and may be promoted to the primary unified path at R3 if it matures.

### Alternative D — adopt CARLA + AWSIM as the AV-specific stack only, defer non-AV sim per actor (REJECTED)

Would work for wadachi but leaves suki, igata, watatsumi, sarutahiko, tatekata each to invent their own sim story. REJECTED because it does not address the cross-actor invariant problem (G5 + cross-actor validation) and reintroduces per-R1 sim re-invention.

### Alternative E — defer this charter entirely; let each actor R1 ADR pick its own sim (REJECTED)

The "do nothing" option. REJECTED because: (a) silently introduces drift; (b) makes future cross-actor sim invariant computation impossible without a costly rewrite; (c) leaves every R1 ADR author personally responsible for the constitutional rejection of NVIDIA proprietary stack, leading to inconsistent rejection language; (d) blocks G5 quantitative quality gate (per-actor reinvention means no shared metric).

### Alternative F — adopt Habitat 3.0 (Meta, Apache 2.0) as the indoor-sim primary (PARTIALLY ADOPTED)

Habitat 3.0 is mature for indoor robotics sim (Apache 2.0; very large indoor dataset). PARTIALLY ADOPTED: Habitat-Matterport 3D asset library is included in the Wave 1 indoor asset list; Habitat 3.0 runtime is NOT adopted as primary because it does not cover AV / outdoor / underwater / industrial-manufacturing sim. Habitat 3.0 runtime may be promoted to a Murakumo cell at R2+ for hagukumi-care / manabi-education indoor robotics sim.

### Alternative G — adopt Pixar RenderMan (closed but free for non-commercial) as the renderer (REJECTED)

RenderMan is closed-source even though some tiers are free. REJECTED for G1 (open architecture invariant) + G14 (30-year reproducibility infeasible).

### Alternative H — adopt Apple Reality Composer / RealityKit (closed) (REJECTED)

Closed-source Apple SDK. REJECTED for G1 + §2(b). Apple-source CC-licensed USD assets MAY be imported under G10 scan and IPFS pinning.

### Alternative I — adopt Blender as the entire authoring + render stack (PARTIALLY ADOPTED)

Blender is GPL-3, which would propagate license contagion if linked into firmware. PARTIALLY ADOPTED: Blender Cycles is consumed via HdCycles (Apache 2.0 Hydra delegate, the Cycles GPL-3 boundary is the delegate process boundary); BlenderProc (GPL-3) is consumed via subprocess invocation (G1 carve-out). Blender's editor itself is not in the substrate runtime.

## References

- ADR-2605192100 — etzhayyim Mission Charter (§1.13 Wellbecoming, §2 anti-secrecy + anti-gatekeeping)
- ADR-2605192200 — etzhayyim IP-Free Release Charter Rider v2.0 (§2(a)-(h))
- ADR-2605215000 — etzhayyim inference Murakumo-fleet-only (no commercial GPU rental)
- ADR-2605231400 — kotoba-datomic Holochain-isomorphic substrate (§4 membrane; attestation lineage)
- ADR-2605242500 — silicon Wave 1 iwakura ternary inference ASIC (future sim-workload hardware path)
- ADR-2605242000 — wadachi autonomous-mobility R&D R0 (consumer of this charter at R1+)
- ADR-2605250500 — yakushi pharmaceutical Tier-B R0
- ADR-2605250715 — tatekata construction Tier-B R0
- ADR-2605252200 — watatsumi civilian-submersible R0
- ADR-2605252400 — kanayama circular metallurgy R0
- ADR-2605252500 — sarutahiko heavy-truck manufacturing R0
- ADR-2605261015 — mitsuho food / agriculture R0
- ADR-2605261115 — makura foam-pillow manufacturing R0
- ADR-2605261200 — igata megacasting / HPDC R0
- ADR-2605261215 — igata R1 benchtop ≤500 ton HPDC commissioning (first eligible R1 consumer of this charter)
- ADR-2605261300 — tsutae handheld communication device R0
- ADR-2605261330 — futawa small-displacement motorcycle manufacturing R0
- ADR-2605261500 — suki farm tractor manufacturing R0
- Pixar OpenUSD — <https://openusd.org/>
- Khronos Vulkan Ray Tracing — <https://www.khronos.org/blog/ray-tracing-in-vulkan>
- MuJoCo MJX (DeepMind) — <https://mujoco.readthedocs.io/en/stable/mjx.html>
- Drake (TRI) — <https://drake.mit.edu/>
- Genesis — <https://genesis-embodied-ai.github.io/>
- HdCycles — <https://github.com/tangent-animation/HdCycles>
- Mitsuba 3 (EPFL) — <https://www.mitsuba-renderer.org/>
- Embree (Intel) — <https://www.embree.org/>
- Brax (Google) — <https://github.com/google/brax>
- BlenderProc (DLR) — <https://github.com/DLR-RM/BlenderProc>
- Kubric (Google) — <https://github.com/google-research/kubric>
- Habitat 3.0 (Meta) — <https://aihabitat.org/>
- CARLA — <https://carla.org/>
- AWSIM (Autoware) — <https://github.com/tier4/AWSIM>
- Project AirSim — <https://microsoft.github.io/AirSim/>
- Isaac Lab (BSD-3, runtime separated) — <https://github.com/isaac-sim/IsaacLab>
- PhysX 5 SDK (BSD-3) — <https://github.com/NVIDIA-Omniverse/PhysX>
