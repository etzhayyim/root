---
id: adr-2605261800-nvidia-omniverse-stack-api-compat
title: "ADR-2605261800: NVIDIA Omniverse Stack API-Compat Layer on KAMI + WebGPU + WASM (e7m-sim R1 sub-charter)"
status: proposed
doc_type: adr
topic: e7m-sim-nv-compat
authoritative: true
last_verified: 2026-05-28
priority: 4.5
axis: architecture
weight: 0.60
priority_note: "Sub-charter under ADR-2605261600 (e7m-sim R0). Expands R1 scope with 9-component API-compat layer."
authoritative_for:
  - e7m-sim/nv-compat
  - 40-engine/kami-engine/kami-rt
  - 40-engine/kami-engine/kami-pbrt
  - 40-engine/kami-engine/kami-usd
  - 40-engine/kami-engine/kami-genesis
  - 40-engine/kami-engine/kami-articulated
  - 40-engine/kami-engine/kami-sensor-sim
  - 40-engine/kami-engine/kami-replicator
  - 40-engine/kami-engine/kami-app-amenominaka
  - kotoba-lang/kami-nv-compat
  - 40-engine/kotoba/crates/kotoba-kotodama/py/kotodama/nv_compat
depends_on:
  - adr-2605261600-robotics-simulation-substrate-r0
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605242000-roso-pattern-frontier-distill
  - adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
  - adr-2605261500-suki-farm-tractor-tier-b-actor-r0
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2607011300-nv-compat-relocation-to-kotoba-lang
supersedes: []
superseded_by: []
---

# ADR-2605261800: NVIDIA Omniverse Stack API-Compat Layer on KAMI + WebGPU + WASM (e7m-sim R1 sub-charter)

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Council Seat 1)

# Context

ADR-2605261600 が `e7m-sim` charter を確立し、NVIDIA proprietary sim stack
(Omniverse / Isaac Sim / Isaac Lab / OptiX / RTX Renderer / Replicator / DriveSim /
Omniverse Cloud / Nucleus) を §2(b) + §2(e) で **N1..N9 = ABSOLUTE NEVER** とした。

一方で religious-corp robotics 群 (wadachi / suki / igata / watatsumi / sarutahiko /
futawa / tatekata / hodoki / makura / tsutae) の R1+ phase では、世界の robotics 開発者・
研究者・農機/トラックメーカー協働者が Omniverse stack 由来の **公開 API surface**
(`omni.usd`, `omni.kit.app`, `omni.replicator.core`, `isaacsim.*`, `isaaclab.*` 等)
に慣れている。**drop-in compat** がなければ religious-corp 外の貢献者が onboard できず、
G14 (30-yr reproducibility) の社会的基盤が脆い。

商標 (Omniverse, Isaac, OptiX, RTX, Nucleus, DriveSim 等) は NVIDIA Corporation の登録商標。
ただし **API シグネチャ自体は事実 (Google v. Oracle, 2021)** で再実装可能。

本 ADR は (i) **9 component を均等に** API-compat 化し、(ii) canonical 実装名は KAMI-native
**和名**を採用し、(iii) compat facade を namespace 局所化することで商標境界を担保する。

物理 backend は **Genesis (Apache-2.0, Genesis-Embodied-AI/Genesis)** を articulated dynamics
の本命に確定。Mitsuba 3 (differentiable rendering) は **upstream PR 路線のみ**、religious-corp
内 fork は持たない。

# Decision

## D1. 9-component API-compat layer 全面 mirror (option b)

NVIDIA stack 9 components 全てに対し canonical KAMI 実装 + nv-compat facade を提供する。

| # | NVIDIA component | KAMI canonical | crate / package | nv-compat facade |
|---|---|---|---|---|
| 1 | Omniverse Kit | **amenominaka** (天之御中) | `40-engine/kami-engine/kami-app-amenominaka/` | `nv-compat/omni-kit-app` |
| 2 | Nucleus | **kotoba-datomic-nucleus** | 既存 kotoba-datomic (MST + IPFS + Base L2) + 新 `com.etzhayyim.sim.usd.layer` Lexicon | `nv-compat/omni-nucleus` |
| 3 | Isaac Sim | **e7m-sim** (R1 articulated phase) | 既存 `70-tools/e7m-sim/` + 新 `kami-articulated` + `kami-genesis` | `nv-compat/isaacsim` |
| 4 | Isaac Lab | **e7m-shugyo** (修行) | 既存 `70-tools/isaac-lab-task-port/` + 新 `kami-shugyo` | `nv-compat/isaaclab` |
| 5 | OptiX | **hikari-rt** (光) | 新 `40-engine/kami-engine/kami-rt/` (WebGPU ray-query + WGSL BVH) | `nv-compat/optix` |
| 6 | RTX Renderer | **kami-rtx** | 新 `40-engine/kami-engine/kami-pbrt/` (Mitsuba 3 WASM bind upstream-only) | `nv-compat/rtx-renderer` |
| 7 | Replicator | **utsushimi** (写身) | 新 `40-engine/kami-engine/kami-replicator/` | `nv-compat/omni-replicator-core` |
| 8 | DriveSim | **wadachi-sim** | 既存 wadachi (ADR-2605242000) + 新 sim layer adapter | `nv-compat/drive-sim` |
| 9 | Omniverse Cloud | **murakumo-render** | 既存 Murakumo fleet + 既存 `kami-rtc` WebRTC streaming | `nv-compat/omni-cloud` |

商標境界: canonical name = 和名 (registry / repo / UI で唯一の正本)。NVIDIA 製品名は
`*/nv-compat/` namespace 内の **import alias** と公開 API mirror docstring にのみ出現。
patent / trademark notice は `CHARTER-RIDER.md` §6 (third-party trademark acknowledgment)
で `NVIDIA®, Omniverse®, Isaac®, OptiX®, RTX®, Nucleus®, DriveSim® are trademarks of
NVIDIA Corporation. This project is not affiliated with or endorsed by NVIDIA.` を明記。

## D2. 物理 backend: Genesis (Apache-2.0) を確定

`kami-genesis` crate (新) が Genesis (Genesis-Embodied-AI/Genesis, Apache-2.0,
Taichi backend) を WebGPU + WASM target で integrate する。

- **integration path**: Genesis Python API → Taichi IR → Vulkan SPIR-V → wgpu (WebGPU)
  compute pipeline。CPU fallback は Taichi `cpu` backend → WASM (Emscripten)
- **覆い scope**: rigid body articulated, MPM (granular / fluid), SPH (liquid),
  FEM (soft body), PBD (cloth) — Genesis の 5 solver 全て対象
- **Isaac Sim API parity**: `isaacsim.core.api.World` / `Articulation` / `RigidPrim`
  / `Joint` を `kami-genesis` の Genesis Scene にマップ
- **non-goal**: Genesis 本体の fork。upstream PR で WebGPU backend を貢献。
  religious-corp 側は `kami-genesis` 薄い bind 層のみ maintain

代替案 (D2 で却下されたもの) は §Alternatives Considered 参照。

## D3. Mitsuba 3 (differentiable rendering): upstream PR only

`kami-pbrt` crate は Mitsuba 3 (mitsuba-renderer/mitsuba3, BSD-3-Clause) の
Dr.Jit → WebGPU compute backend を **upstream に PR で貢献**する。religious-corp
は `mitsuba3-fork/` を持たず、上流が merge するまで PoC は `kami-pbrt/poc-patches/`
に時限 patch (max 90 日、自動消滅) として保持。

90 日経過時点で upstream に merge されない場合、本 ADR §D3 を再評価し ADR-2605261800-r1
で fork 化 or 代替 (Falcor / pbrt-v4) 移行を決定する。

## D4. WebGPU + WASM target invariant (baien edge-target 整合)

ADR-2605241900 baien edge-target invariant に従い、**iPhone 12+ / Android 4GB / WASM-32**
の 3 環境すべてで minimum viable render が動作すること。

- **hardware RT**: Chrome 121+ `ray-query` extension がある場合のみ enable、
  なければ WGSL software BVH fallback (LBVH compute build)
- **memory ceiling**: client-side heap ≤2GB @4k tri, ≤2.5GB @16k tri (baien 同条件)
- **GPU offload**: 重量 compute (path tracing >50k tri, MPM >100k particle 等) は
  `murakumo-render` 経由で Murakumo fleet (EVO-X2 + Mac mini cluster) に offload、
  WebRTC で result stream-back。**RunPod / commercial GPU rental は §2(b) NEVER**
- **mobile fallback**: iPhone Safari WebGPU は実用、Android WebGPU は Chrome 121+ のみ。
  WebGL2 final fallback で raster path は維持 (RT は無効化)

## D5. API mirror 形式 (drop-in import alias)

**Python** (kotodama / e7m-sim 利用者):

```python
# 既存 Omniverse Python script
import omni.usd
import omni.kit.app
import omni.replicator.core as rep
from isaacsim.core.api import World
from isaaclab.envs import ManagerBasedRLEnv

# nv-compat 利用版 (import 経路差し替えのみ、本文同一)
import kotodama.nv_compat.omni.usd as omni_usd
import kotodama.nv_compat.omni.kit.app as kit_app
import kotodama.nv_compat.omni.replicator.core as rep
from kotodama.nv_compat.isaacsim.core.api import World
from kotodama.nv_compat.isaaclab.envs import ManagerBasedRLEnv
```

**TypeScript** (etzhayyim-sdk 利用者):

```typescript
// canonical KAMI-native (推奨)
import { App, World, Robot, Sensor, Renderer, Replicator }
  from '@etzhayyim/sdk/sim'

// nv-compat (drop-in for porting existing Omniverse Kit / Isaac Sim TS bindings)
import { Stage, Layer } from '@etzhayyim/sdk/nv-compat/omni-usd'
import { Application }  from '@etzhayyim/sdk/nv-compat/omni-kit-app'
import { World as IsaacWorld }
  from '@etzhayyim/sdk/nv-compat/isaacsim/core/api'
```

API mirror は **公開 docs に記載のある public API surface のみ**。Omniverse Kit の
private / 内部 API、未文書化 binding は対象外。本制限は `README.md` および各
nv-compat package の頭で明記する (N7)。

## D6. Workspace 追加 (10 新 crate + 2 SDK namespace)

```
40-engine/kami-engine/                     # 新 crate 7
├── kami-rt/                               # hikari-rt: WGSL ray-query + LBVH compute
├── kami-pbrt/                             # kami-rtx: Mitsuba 3 WASM bind (upstream-only)
├── kami-usd/                              # tinyusdz WASM + Hydra render delegate
├── kami-genesis/                          # Genesis Taichi → WebGPU bind
├── kami-articulated/                      # URDF / MJCF / USD physics → kami-genesis
├── kami-sensor-sim/                       # camera / lidar / IMU / contact synth
├── kami-replicator/                       # utsushimi: DR + SDG pipeline
├── kami-app-amenominaka/                  # app shell + extension loader
└── kami-shugyo/                           # e7m-shugyo: RL gym + curriculum

20-actors/etzhayyim-sdk/src/
├── sim/                                   # canonical TS API (App, World, Robot, ...)
└── nv-compat/                             # NVIDIA API mirror facade
    ├── omni-usd.ts
    ├── omni-kit-app.ts
    ├── omni-replicator-core.ts
    ├── omni-nucleus.ts
    ├── isaacsim/{core,sensors,robots}.ts
    ├── isaaclab/{envs,tasks,managers}.ts
    ├── optix.ts
    ├── rtx-renderer.ts
    ├── drive-sim.ts
    └── omni-cloud.ts

40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/
├── sim/                                   # canonical Python API
└── nv_compat/                             # NVIDIA Python API mirror
    ├── omni/{usd, kit/app, replicator/core, nucleus}.py
    ├── isaacsim/{core, sensors, robots}/
    ├── isaaclab/{envs, tasks, managers}/
    └── ...

70-tools/e7m-sim/                          # 既存
├── scenes/                                # USD reference scenes
├── benches/                               # G5 quality gate measurements
└── compat-tests/                          # NEW: NV script port-and-run regression suite
```

## D7. Phase 計画 (e7m-sim R1 sub-phases)

| Sub-phase | Scope | Gate (G5 quality gate per ADR-2605261600) |
|---|---|---|
| **R1.0** (本 ADR 採択時) | 10 crate path reservation, deps.toml 登録, nv-compat README stub | Council acknowledge |
| **R1.1** | `kami-usd` + `kami-genesis` rigid + Cartpole / Pendulum gym 動作 | Isaac Sim 同 task reward curve ±10% (1000 episode) |
| **R1.2** | `kami-rt` (WGSL ray-query) + `kami-pbrt` Cornell box | PSNR ≥ 35dB vs Mitsuba 3 CUDA reference |
| **R1.3** | `utsushimi` + BasicWriter API parity + 1k img dataset | `omni.replicator.core` 同 script で同 output schema (JSON diff = 0) |
| **R1.4** | `kami-app-amenominaka` extension loader + 5 Omniverse extension 動作 | omni.usd / omni.kit.app / omni.replicator.core / omni.kit.viewport / omni.timeline |
| **R1.5** | `kami-shugyo` + Franka pick-and-place task | Isaac Lab task DSL drop-in、success rate ≥ Isaac Lab baseline × 0.8 |
| **R1.6** | `wadachi-sim` DriveSim parity (sensor + scenario DSL) | wadachi R2 input scenario coverage 80% |
| **R1.7** | `murakumo-render` cloud streaming | iPhone 12 で Cornell box realtime (30 fps) via WebRTC |
| **R1.8** | `kami-genesis` MPM/SPH/FEM/PBD coverage | igata megacasting flow sim PoC (granular) + hagukumi cloth sim PoC |
| **R1.9** | kotoba-datomic-nucleus USD layer diff Lexicon + 5-member collab demo | 5-member concurrent edit on 1 stage, conflict resolve <2s |

G5 quality gate (≥ 0.75 vs Isaac Sim) は **PSNR / SSIM / Chamfer / IoU / sim-to-real**
の 5 軸を sub-phase 毎に測定し `70-tools/e7m-sim/benches/sub-phase-{N}.jsonl` に
kotoba-datomic attestation 付きで commit。

## D8. License & 商標 boundary (Charter Rider 整合)

- canonical crate 全てに **Apache 2.0 + Charter Compliance Rider v2.0** (`/CHARTER-RIDER.md`)
- Genesis (Apache 2.0, upstream): vendored `lib/genesis/` (charter-rider-applicator skip)
- Mitsuba 3 (BSD-3): vendored `lib/mitsuba3/` (charter-rider-applicator skip)
- tinyusdz (Apache 2.0): vendored `lib/tinyusdz/` (charter-rider-applicator skip)
- 商標 disclaimer: `CHARTER-RIDER.md` §6 に NVIDIA trademark notice 追加 (本 ADR D1 +
  §D11 amendment で PhysX® 追記)
- nv-compat facade 内のシンボル名は **public API mirror として最小限**、独自 enhancement や
  branding は禁止 (canonical 側に追加すること)

## D10. WASM + WebGPU viability gate → from-scratch fallback (amendment 2026-05-26)

religious-corp の WASM + WebGPU edge-target invariant (ADR-2605241900 + 本 ADR §D4) は
**hard rule**。upstream backend (Genesis / Mitsuba 3 / tinyusdz / BlenderProc 等) が
この invariant を満たさない場合、religious-corp は **当該機能を KAMI namespace 内で
0 から WASM + WebGPU 設計実装** する。

### D10.1 viability gate

各 upstream backend に対し sub-phase 単位の **viability gate** を設定:

| Backend | Gate | Deadline | Pass criteria |
|---|---|---|---|
| Genesis (rigid solver) | R1.1 | 2026 Q3 | iPhone 12+ Safari で Cartpole 60 fps、heap ≤2GB |
| Mitsuba 3 (differentiable render) | R1.2 | 2026 Q4 | Chrome 121+ で Cornell box 30 fps、PSNR ≥35dB |
| tinyusdz (USD parse) | R1.1 | 2026 Q3 | iPhone 12+ で 10MB USD ≤2s parse |
| Genesis (MPM/SPH/FEM/PBD) | R1.8 | 2027 H1 | EVO-X2 で 100k particle 30 fps |
| BlenderProc (synth data subprocess) | R1.3 | 2026 Q4 | Murakumo node で 1k img/hr |

### D10.2 fallback 発動条件

deadline 時点で gate が pass しない場合:

1. **Council Lv6+ ≥3 attestation** で fallback 発動を確定
2. 該当機能の **KAMI-native crate** を新規追加 (path 既予約、§D10.4 参照)
3. **nv-compat facade は変更不要** (内部 backend swap のみ; D5 import alias 仕様は不変)
4. fallback 進捗を `90-docs/baien/sim-fallback-{backend}-{date}.md` に記録

### D10.3 fallback 後の API parity 保証

backend が swap されても **D5 で定めた drop-in import alias は変わらない**:

```python
# upstream Genesis でも、KAMI-native fallback でも、import 経路は同一
from kotodama.nv_compat.isaacsim.core.api import World, Articulation
```

これは Google v. Oracle (2021) の API fair use を religious-corp 側で完全担保する設計。

### D10.4 fallback crate path reservations (R1.0 で予約)

| Fallback crate | Triggered by | Scope | Scaffold path |
|---|---|---|---|
| `kami-physics-solvers` | Genesis WebGPU が R1.1 / R1.8 gate fail | 5 solver (rigid Featherstone + XPBD / MPM / SPH / FEM / PBD) を WGSL compute で 0 から実装 | `40-engine/kami-engine/kami-physics-solvers/` |
| `kami-rtx-native` | Mitsuba 3 wgpu PR が R1.2 gate fail | path tracer + differentiable rendering を `kami-rt` + WGSL の上に 0 から実装 | `40-engine/kami-engine/kami-rtx-native/` |
| `kami-usd-native` | tinyusdz WASM が R1.1 gate fail | USD Crate / ascii / binary parser + composition engine を Rust で 0 から実装 | `40-engine/kami-engine/kami-usd-native/` |

### D10.5 工数 honest framing

from-scratch fallback は upstream bind の **5-10×** 工数。religious-corp が
fallback を発動するということは:

- 単なる integration から **multi-year robotics R&D commitment** への移行を意味する
- Council Lv6+ ≥3 attestation が **政策決定** として要求される所以
- iwakura ASIC Wave 1 silicon (ADR-2605242500) が ready になるタイミングで
  fallback が CUDA 依存を完全に切断できる利点と引き換え

religious-corp が fallback を選ぶ場合の判断軸:
1. ADR-2605241900 edge-target invariant の hard 性
2. 30-year reproducibility (G14) — upstream が消えても religious-corp が独立して
   動かせる substrate を確保
3. iwakura ASIC silicon Wave 1 への absorption path — fallback crate は最初から
   Vulkan SPIR-V → iwakura ISA 経路を見据えて設計

## D11. PhysX API parity 追加 (10th compat target, amendment 2026-05-26)

D1 表に **10 番目の compat target = PhysX** を追加:

| # | NVIDIA component | KAMI canonical | nv-compat facade |
|---|---|---|---|
| 10 | PhysX | **kami-physx** (compat layer over kami-genesis or kami-physics-solvers fallback) | `nv-compat/physx` |

### D11.1 PhysX 選定理由

- PhysX 5 SDK は **BSD-3-Clause** (NVIDIA-Omniverse/PhysX-5 GitHub) で license 整合
- PhysX 4.x も `omni.physx` 経由で Omniverse Kit と密結合 — PhysX compat なしで
  Isaac Sim port は実質不可能
- PxScene / PxRigidDynamic / PxArticulationReducedCoordinate / PxShape /
  PxJoint 等の API surface mirror で wadachi / suki / sarutahiko R1+ の rigid
  body sim が drop-in port 可能

### D11.2 PhysX implementation 方針

優先順:
1. **PhysX 5 SDK WASM build** が religious-corp 利用可能な品質で upstream に
   存在 → 直接 integrate (BSD-3 vendor 許容)
2. 1 が無い場合 → **kami-genesis rigid solver で PhysX API surface mirror**
3. 1 + 2 両方 fail → **kami-physics-solvers fallback** (§D10.4) で 0 から PhysX
   API surface 実装

### D11.3 trademark 整合

PhysX® は NVIDIA Corporation の登録商標。CHARTER-RIDER.md §6.1 の trademark
notice list に追加する (D1 + D8 と同パターン)。

## D12. TS-side surface progress (amendment 2026-05-28; iter 71–109 of /loop)

`@etzhayyim/sdk/nv-compat` (D6 + D7 R1.0) は当初 path-reservation 想定だったが、
`/loop` セッション (prompt: "robotics 関係で nvidia family を webgpu, wasm で
実装、再現するのにまだ足りていないのは? それを実装") の iter 71–109 で
**TS-side surface を R1.1 kami-genesis bind 着地前に先行 ship** した。これは
ADR を変更するものではなく、D7 phase 表の R1.0 達成範囲を **honest framing**
として記録する amendment である。

### D12.1 Sub-namespace 構成 (iter 109 時点)

| Sub-namespace | 実装範囲 | Iter |
|---|---|---|
| `dynamics/` | Featherstone ABA + RNEA + CRBA + FK + 幾何 Jacobian + DLS IK / URDF parser (regex, XML dep なし) | 71–82 |
| `controllers/` | PD joint controller | 100 |
| `actions/` | action scale+clamp / effort_limit τ saturation | 101 / 102 |
| `assets/` | Franka FCI 7-DoF (real joint origins) / ANYmal C 12-DoF branched (ANYbotics public) / UR10 6-DoF (ur_description BSD-3) | 83 / 91 / 98 |
| `warp/` | ~16 WGSL kernels — `damping` / `pendulum` / `cartpole` / `twoLink` / Franka `fk` + `jacobian` + `reach` + `gravComp` / `anymalFk` / `genericSerialFk` N≤12 / `pdJointController` / `actionScaleClamp` / `effortLimit` / `observationNormalize` + `gaussianMarsaglia` + `mulberry32` / `l2NormSquared` + `trackVelExp` + `combineWeightedRewards` / `terminations` / `mlpPolicyForward` / `conditionalReset` / `groundContact` (spring-damper normal force) | 85–109 |
| `policies/` | MLP v1 JSON checkpoint loader (`type:'mlp_policy'` / strict dim validation / He-init random fixture / `runMlpPolicy` wrapper) | 108 |

### D12.2 End-to-end Isaac Lab task loop closed in WebGPU/WASM

```
raw_obs → observationNormalize (+ Gaussian noise)
       → mlpPolicyForward (Linear → ReLU → Linear → tanh)
       → actionScaleClamp → pdJointController → effortLimit
       → ABA (forward dynamics) → integrate
       → l2NormSquared / trackVelExp → combineWeightedRewards
       → terminations (joint-limit + fall + timeout)
       → conditionalReset (per-env done flag)
       → next obs
```

Ground-plane contact (iter 109) は **normal force only** (frictionless); Coulomb
friction tangent forces (`|F_t| ≤ μ·F_n` cone) は iter 110+ で追加予定。

### D12.3 Compile-bound 制約 (mobile WebGPU safety)

WGSL kernel は MAX を **compile-bound + runtime n 早期 exit** で構造化:

- `genericSerialFk`: `MAX_N_SERIAL_FK = 12`
- `terminations`: `MAX_N_TERM = 32`
- `mlpPolicyForward`: `MAX_HIDDEN_MLP = 128`, `MAX_OBS_MLP = 64`

これにより per-thread `array<f32, N>` が iPhone 12+ Safari の 32KB/workgroup
limit に収まり、D4 baien edge-target invariant (≤2GB heap @4k ctx) を堅持する。

### D12.4 Persistent regression guard

`20-actors/etzhayyim-sdk/test/nv-compat-cross-validation.test.ts` — **69 test
WGSL ↔ JS reference cross-validation**、wall 13–31 ms。新しい kernel が landing
するたびに describe block を追加する pattern が確立 (iter 86 で 15 test として
seed → iter 109 時点で 69 test)。byte-identity guarantee (CPU 上の inline JS
reference と WGSL kernel が ±1 ULP 同期) を毎 commit で確認する。

### D12.5 D7 phase 表に対する位置付け

D7 R1.0 = 「10 crate path reservation, deps.toml 登録」想定だったが、iter 71–109
で **TS-side surface (sub-namespace 6 個 + WGSL 16 kernel + 3 vendor asset + 69
test)** が landed。これは **R1.1 (kami-genesis rigid + Cartpole gym) 着地前の
ahead-of-schedule deliverable** と解釈し、D7 phase 表は変更しない (R1.1+ の
kami-genesis bind / Isaac Sim 同 task reward curve ±10% gate は依然未達)。

`40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/nv_compat` (Python-side facade) は
ADR-2605261800 commit 時の Cartpole PoC 6 facade module (R1.1 Phase B) で
止まっており、TS-side の advanced surface は **未 mirror**。Python ↔ TS parity
は R1.2+ で kami-genesis bind が両側で同時に動いた時点で揃える。

# Consequences

## Positive

- **drop-in port**: 既存 Omniverse / Isaac script が import 1 行差し替えで動作
- **5 solver coverage**: Genesis 採用で rigid + MPM + SPH + FEM + PBD を 1 backend に統一
  (MJX なら rigid only)
- **edge-target reach**: WebGPU + WASM 路線で iPhone / Android で robotics sim 教育・
  prototype が動作 (Omniverse は Linux x86_64 + NVIDIA GPU 必須)
- **vendor-neutral GPU**: Apple Metal / Adreno / Mali / iwakura ASIC Wave 1 全対象
- **religious-corp 外貢献者の onboarding**: Omniverse 経験者がそのまま貢献可

## Negative

- **工数 大**: 10 新 crate + 2 SDK namespace。R1.0–R1.9 で 2026 H2 + 2027 H1
- **Genesis WebGPU 未成熟**: Taichi の Vulkan/WebGPU backend は CUDA 比で性能差大、
  R1.1 で実測ベンチ後に scope 再調整あり得る
- **Mitsuba 3 upstream merge 不確実性**: 90 日 deadline で fork 化判断あり得る (D3)
- **public API mirror の覆い率**: NVIDIA Kit 全 API の ~70% (公開分) が現実的、
  100% は不可能 (N7 明記)
- **G5 quality gate (≥0.75 vs Isaac Sim)** の達成は R1.4 時点で 60-65% 想定、
  R1.7+ で iwakura ASIC capacity 入って初めて 75% 到達見込

## Non-goals (絶対しない)

| N | 内容 | 根拠 |
|---|---|---|
| N1 | Omniverse Kit / Nucleus / Isaac Sim / Isaac Lab / OptiX / RTX Renderer / Replicator / DriveSim / Omniverse Cloud のバイナリ・SDK・ヘッダのリンクまたは redistribution | ADR-2605261600 §2(b)+(e); 本 ADR D1 |
| N2 | NVIDIA 商標 (Omniverse, Isaac, OptiX, RTX, Nucleus, DriveSim) を canonical package 名・class 名・公開 UI に使用 | 商標侵害回避。nv-compat namespace 局所化 (D1) |
| N3 | CUDA / OptiX / cuDNN / TensorRT / Triton kernel への直接依存 | ADR-2605261600 §2(b) vendor-neutral GPU 不変条件 |
| N4 | RunPod / commercial cloud GPU rental による offload | ADR-2605215000 Murakumo-only; D4 |
| N5 | 軍事 robotics / 兵器 sim payload (target tracking, weapon trajectory, etc.) | Charter §2(a) |
| N6 | 監視・大規模顔認識 sim asset (CCTV scene library, face DB, etc.) | Charter §2(c) |
| N7 | API parity を「100%」と謳う | NVIDIA Kit は closed。公開 docs にある public API surface のみが対象 |
| N8 | Mitsuba 3 / Genesis / tinyusdz の religious-corp 内 fork を maintain | D2, D3, D8 — upstream 貢献路線 |
| N9 | Omniverse Kit private API / undocumented binding の re-export | nv-compat は公開 API のみ (D5) |
| N10 | nv-compat namespace 内で canonical 機能拡張 / branding 追加 | nv-compat は薄い alias のみ (D8) |

## Constitutional checks

- ✅ Charter §2(a) 兵器: N5
- ✅ Charter §2(b) commercial GPU rental: D4 + N4
- ✅ Charter §2(c) 監視: N6
- ✅ Charter §2(e) closed-source vendor stack: N1 + N3
- ✅ Charter §2(i) GPU rental (ADR-2605215000): D4 + N4
- ✅ ADR-2605241900 baien edge-target invariant: D4
- ✅ ADR-2605261600 e7m-sim §2(b)+(e): D1 nv-compat namespace 局所化で trademark 境界明示

## Deps.toml entries (R1.0 で追加予定)

```toml
[[adrs]]
id = "ADR-2605261800"
slug = "nvidia-omniverse-stack-api-compat"
status = "proposed"
date = "2026-05-26"
authoritative_for = ["e7m-sim/nv-compat", "kami-rt", "kami-pbrt", "kami-usd",
                     "kami-genesis", "kami-articulated", "kami-sensor-sim",
                     "kami-replicator", "kami-app-amenominaka", "kami-shugyo"]

[[modules]]
path = "40-engine/kami-engine/kami-rt"
adr  = "ADR-2605261800"
[[modules]]
path = "40-engine/kami-engine/kami-pbrt"
adr  = "ADR-2605261800"
[[modules]]
path = "40-engine/kami-engine/kami-usd"
adr  = "ADR-2605261800"
[[modules]]
path = "40-engine/kami-engine/kami-genesis"
adr  = "ADR-2605261800"
[[modules]]
path = "40-engine/kami-engine/kami-articulated"
adr  = "ADR-2605261800"
[[modules]]
path = "40-engine/kami-engine/kami-sensor-sim"
adr  = "ADR-2605261800"
[[modules]]
path = "40-engine/kami-engine/kami-replicator"
adr  = "ADR-2605261800"
[[modules]]
path = "40-engine/kami-engine/kami-app-amenominaka"
adr  = "ADR-2605261800"
[[modules]]
path = "40-engine/kami-engine/kami-shugyo"
adr  = "ADR-2605261800"
[[modules]]
path = "20-actors/etzhayyim-sdk/src/nv-compat"
adr  = "ADR-2605261800"
[[modules]]
path = "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/nv_compat"
adr  = "ADR-2605261800"
```

# Alternatives Considered

## A1. Physics backend 候補

| Candidate | License | WebGPU path | 採否理由 |
|---|---|---|---|
| **Genesis** (Genesis-Embodied-AI) | Apache-2.0 | Taichi → Vulkan → wgpu (upstream PR 必要) | **採択** — 5 solver 統一 (rigid/MPM/SPH/FEM/PBD)、Isaac Sim 性能超過実績 |
| MuJoCo MJX (Google DeepMind) | Apache-2.0 | JAX/XLA → 要 WebGPU backend port | 却下 — rigid only、MPM/FEM 別 backend 必要、当初候補だが scope 不足 |
| Drake (TRI/MIT) | BSD-3 | C++ heavy, WASM port 重い | 却下 — robot-centric だが WASM target 不利 |
| NVIDIA Newton (preview) | unknown | CUDA-only | 却下 — closed-source 路線 (§2(b) + §2(e)) |
| Bullet (Erwin Coumans) | zlib | C++ → WASM 既存 (Ammo.js) | 却下 — articulated は弱い、MPM/SPH なし |
| PhysX (NVIDIA) | BSD-3 (5.x) | CUDA-optional だが GPU path は CUDA | 却下 — vendor-neutral GPU 不変条件違反 (D4 + N3) |

## A2. Rendering backend 候補

| Candidate | License | WebGPU path | 採否理由 |
|---|---|---|---|
| **Mitsuba 3 + KAMI wgpu** | BSD-3 + 自前 | Dr.Jit → wgpu backend (upstream PR) | **採択** — differentiable + offline 両対応、scientific community 信頼 |
| Falcor (NVIDIA) | BSD-3 | DirectX/Vulkan only, no WebGPU | 却下 — NVIDIA branding, WebGPU port 大規模 |
| pbrt-v4 | BSD-2 | C++ → WASM 可だが realtime 不可 | 却下 — offline 専用 |
| Filament (Google) | Apache-2.0 | WebGL only, no path tracing | 却下 — raster only |

## A3. API parity 範囲

| Option | 内容 | 採否 |
|---|---|---|
| (a) 4 本柱に絞る (Replicator + USD + Kit + Isaac Lab) | scope 限定で R1 早期達成 | 却下 |
| **(b) 全 9 component 均等** | drop-in port の cover 最大化 | **採択** (user decision) |
| (c) Isaac Lab + Replicator 優先 + 他 stub | RL training 用途特化 | 却下 |

## A4. Compat facade 配置

| Option | 採否 |
|---|---|
| canonical と nv-compat を同一 package 内 | 却下 — 商標境界が曖昧 |
| **nv-compat を独立 namespace (`nv-compat/`)** | **採択** — trademark 局所化 + import alias で drop-in 達成 |
| nv-compat を別 repo (`etzhayyim/nv-compat`) | 却下 — monorepo 原則違反 (Shannon 重複) |

## A5. Mitsuba 3 fork 戦略

| Option | 採否 |
|---|---|
| **upstream PR only (max 90 日 hold)** | **採択** (user decision) — fork 維持コスト回避 |
| 即 fork (`mitsuba3-fork/`) | 却下 — upstream 維持 + Shannon 重複 |
| Mitsuba 3 を捨てて自前 path tracer | 却下 — scientific credibility 喪失 |

# References

- ADR-2605261600 (Robotics simulation substrate R0 charter — 本 ADR の親)
- ADR-2605215000 (etzhayyim inference Murakumo-only, no RunPod)
- ADR-2605241900 (Baien edge-target invariant — iPhone 12+ / Android 4GB / WASM-32)
- ADR-2605192100 (etzhayyim mission charter — §1.12 + §2(b) + §2(e))
- ADR-2605192200 (Charter Rider v2.0 — license + trademark boundary)
- ADR-2605242000 (wadachi autonomous mobility R&D R0)
- ADR-2605252500 (sarutahiko heavy truck mfg R0)
- ADR-2605261500 (suki farm tractor R0)
- ADR-2605231400 (kotoba-datomic Holochain-iso substrate — nucleus 等価層)
- 40-engine/kami-engine/CLAUDE.md (KAMI engine architecture)
- 70-tools/e7m-sim/ (R0 scaffold, ADR-2605261600)
- Genesis-Embodied-AI/Genesis (Apache-2.0, https://github.com/Genesis-Embodied-AI/Genesis)
- mitsuba-renderer/mitsuba3 (BSD-3, https://github.com/mitsuba-renderer/mitsuba3)
- lighttransport/tinyusdz (Apache-2.0, https://github.com/lighttransport/tinyusdz)
- Google v. Oracle, 593 U.S. ___ (2021) — API シグネチャ再実装 fair use 判例
