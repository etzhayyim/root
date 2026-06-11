---
id: adr-0031-kami-vrm-three-free-topology
title: "ADR-0031: KAMI VRM three.js-free topology"
status: active
doc_type: adr
topic: vrm-runtime
authoritative: true
last_verified: 2026-04-18
related: []
supersedes: []
superseded_by: []
---

# ADR-0031: KAMI VRM three.js-free topology

**Status**: active
**Date**: 2026-04-18
**Scope**: `40-engine/kami-engine/kami-vrm`, `kami-render`, `kami-web`, `kami-engine-sdk`, VRM-consuming apps (baminiku / yoro / isekai ...)

## Context

Until 2026-04-17 the VRM avatar viewer in `@etzhayyim/kami-engine-sdk` relied on **three.js + `@pixiv/three-vrm`** at runtime for:

- Scene graph + WebGL renderer
- VRM skeletal deformation
- VRM expression/morph target blending
- Spring bone physics + `VRMC_node_constraint` evaluation
- Part composition (hair/outfit swap in `createPartComposer`)

`kami-web` (wgpu WASM entry) rendered only static VRM meshes via `run_embed_vrm`. Skeletal, morph, spring, and constraint features were absent on the wgpu path, so every real consumer (baminiku, yoro profile header, isekai, sabiotoshi) bundled three.js + `@pixiv/three-vrm`, roughly **+640 kB gzipped** per consumer.

This contradicts `40-engine/kami-engine/CLAUDE.md`'s "wgpu 統一レンダラ" mandate and blocks further Shannon work (every VRM change required dual-path updates).

## Decision

Render VRM end-to-end on the KAMI wgpu WASM path. Retire three.js + `@pixiv/three-vrm` as runtime dependencies of the avatar viewer; retain them only as **optional** peer deps for the legacy preset-swap surface in `createPartComposer` until a wgpu-native composer ships.

### Runtime topology (authoritative)

```
GLB bytes (.vrm)
  ├─→ kami_render::gltf_loader::load_glb      [core glTF 2.0 + JOINTS_0 / WEIGHTS_0 / invBind / node hierarchy]
  │     └─ GltfScene { meshes, materials, textures, morph_targets, skins, node_hierarchy, skin_joints, skin_weights }
  └─→ kami_vrm::parse_vrm                     [VRMC_vrm, VRMC_springBone, VRMC_node_constraint]
        └─ VrmDocument { humanoid, spring_bones, spring_bone_colliders, node_constraints, ... }

kami_vrm::{spring,constraint}::* (pure Rust, no gpu dep)
  SpringSimulator  — verlet chain + sphere/capsule colliders (VRMC_springBone)
  ConstraintSolver — Rotation / Aim / Roll (VRMC_node_constraint)

kami_web::run_embed_vrm (wasm-bindgen entry)
  Per-frame:
    1. Compute user-pose world transforms from pose_overrides
    2. SpringSimulator.step → patch overrides
    3. ConstraintSolver.apply → patch overrides
    4. compute_pose_palette(Skeleton, effective_overrides) → upload bone storage buffer
    5. GPU skinning (56B vertex, Uint16x4 joints + Float32x4 weights) + GPU morph (per-batch delta storage + weights uniform) + MToon fragment

JS surface (kami-engine-sdk / createVrmEngine)
  engines: ['kami']  (default, three.js path removed)
  Controllers drive wasm exports:
    - runEmbedVrm / setVrmMorph{,ByName} / resetVrmMorphs / setVrmCamera
    - setVrmBoneRotation / resetVrmPose / getVrmBoneNames / getVrmSkeletonInfo
    - getVrmMeshLabels / setVrmMeshVisibility (L8 — batch visibility for part composer)
```

### What three.js is no longer responsible for

| Layer | Before | After |
|---|---|---|
| Static mesh render | three WebGLRenderer | kami-render wgpu (MToon + PBR pipelines) |
| GPU skinning | three SkinnedMesh | `skinned_mtoon.wgsl` + 56B skinned vertex + bone palette storage buffer |
| GPU morph | three morph target weights | per-batch storage deltas + `MorphInfo` uniform (weights in vertex shader) |
| Pose / bones | three Object3D.quaternion | `set_vrm_bone_rotation` + thread-local `pose_overrides` |
| Spring bones | `@pixiv/three-vrm` springs | `kami_vrm::spring::SpringSimulator` (verlet + sphere/capsule colliders) |
| Node constraints | `@pixiv/three-vrm` constraints | `kami_vrm::constraint::ConstraintSolver` |
| Part visibility | `obj.visible = false` | `set_vrm_mesh_visibility` (per-batch label, render-loop skip) |
| Part preset swap | three GLTFLoader + VRMLoaderPlugin | **TODO** — use `kami_vrm::compose` + reload |

### SDK contract

`createVrmEngine.svelte.ts`

- `engines?: ('kami')[]` — default `['kami']` (was `('kami' | 'three')[]` defaulting to `['three']`).
- `initThree()` + all `await import('three'|'three/addons/*'|'@pixiv/three-vrm')` deleted.
- Animation loop no longer drives three rendering; KAMI owns RAF internally. The JS tick advances motion state (`motionCtrl.evaluate(time)`) + auto-blink via the KAMI morph export only.
- `state.three` retained as `null` for backwards type compatibility; marked for removal in a future minor version.

`createPartComposer.svelte.ts`

- Uses `getVrmMeshLabels` + `setVrmMeshVisibility` instead of three scene traversal.
- `loadPresetPart` / `setHairStyle` / `setHairColor` / `setOutfitStyle` / `setOutfitColor` — stubbed with `console.warn`. The wgpu-native implementation is tracked as follow-up work (Migration section below).

`package.json`

- `three` and `@pixiv/three-vrm` move from required `peerDependencies` to `peerDependenciesMeta.optional = true`.
- `@types/three` moves from `devDependencies` to unused (kept off the lockfile).
- Consuming apps (baminiku) drop `three` / `@pixiv/three-vrm` / `@types/three` outright.

## Topology constraints (CRITICAL)

1. **`kami_vrm` is VRM domain logic only** — no wgpu / render / web-sys dependencies. It is a pure Rust crate consumed by both native tools (`etzhayyim vrm ...`) and the wgpu path. Adding a gpu dep here violates the topology.
2. **`kami_render::gltf_loader` is the single glTF loader** — additive expansion (JOINTS_0/WEIGHTS_0/invBind/hierarchy/mesh+material labels) is allowed; parallel loaders in app code are forbidden.
3. **`kami_web::run_embed_vrm` is the single VRM entry** — per-feature new wasm-bindgen exports (`get_vrm_*` / `set_vrm_*`) are allowed when they map cleanly to a VRM spec surface. New renderer pipelines belong in `kami-render`.
4. **The SDK is a thin facade** — controllers (`createMorph` / `createBone` / `createMotion` / `createPart`) dispatch to KAMI wasm exports. No parallel rendering implementation.
5. **`kami-web` stays the VRM entry point** — the "per-game wasm bundle" pattern (see `60-apps/CLAUDE.md` §Per-Game WASM Pattern) applies to games, not to avatar viewers. VRM viewing is a single contract shared across consumers.

## Layer history (2026-04-17 → 2026-04-18)

| Layer | Landed | Commit |
|---|---|---|
| L1 skin data extraction (JOINTS_0/WEIGHTS_0/invBind/hierarchy) | 2026-04-17 | `26d76605e` |
| L2 Skeleton reconstruction + `get_vrm_skeleton_info` | 2026-04-17 | 〃 |
| L3 GPU skinning pipeline (`skinned_mtoon.wgsl`) | 2026-04-17 | `b80470cf4` |
| L4 pose API + per-frame bone palette upload | 2026-04-17 | `83f6153a4` |
| L5 GPU morph (storage deltas + weights uniform) | 2026-04-17 | `604d88a8b` |
| SDK integration (baminiku engines: ['kami']) | 2026-04-17 | `d7a7c6f51` |
| L6 spring bone simulator | 2026-04-17 | `bc72b1c8d` |
| L7 node constraint solver | 2026-04-17 | 〃 |
| L6 colliders (sphere + capsule) | 2026-04-18 | `cbc130654` |
| three.js drop (createVrmEngine, baminiku deps) | 2026-04-18 | 〃 |
| L8 part composer (wgpu visibility API) | 2026-04-18 | this commit |

## Consequences

### Positive

- **VRM viewer bundle**: baminiku VRM path loses three (~550 kB min+gzip) + three-vrm (~85 kB) = **~635 kB removed**. kami-web wasm is **~1.9 MB** but amortized across all wgpu features (terrain, voxel, VRM, graph, ...). Per-viewer delta ≈ -600 kB vs previous three-backed viewer.
- **Single contract** — `kami_web::run_embed_vrm` + the wasm-bindgen export set is the sole VRM rendering surface. All consumers share the same code path, pipeline version, and performance characteristics.
- **Domain separation** — VRM spec compliance (parse, spring, constraint, part composition) lives in `kami-vrm`. Render-side concerns (pipelines, shaders, bind groups) live in `kami-render` / `kami-web`. No cross-layer leakage.
- **No three lock-in** — future VRM features (IK, blend tree, sidecar animation retargeting) can be added natively without reconciling two engines.

### Negative / migration cost

- **Preset part swap temporarily regressed** — `createPartComposer.loadPreset*` is a no-op. Existing consumers that relied on hair/outfit swap (primarily `sabiotoshi`) must either:
  - use base-VRM part toggling via `togglePart` (already works), **or**
  - defer preset UI until the wgpu composer lands (see Migration).
- **createPartComposer API shift** — `three: ThreeVrmHandle | null` → `kami: KamiWasmExports | null`. Downstream code must pass the KAMI handle instead of three handle.
- **No opt-in three fallback** — consumers with stale wgpu drivers (pre-Chrome 113 / Firefox 116) will not render. Acceptable given WebGPU is at ~97% browser coverage per `40-engine/kami-engine/CLAUDE.md`.

### Migration (for consumers)

1. Audit every `createVrmEngine({ engines: ['three'] })` or `['kami', 'three']` call site; change to `['kami']` (or omit — it's the default now).
2. Audit every `createPartComposer({ three: ... })` call site; change to `createPartComposer({ kami: engine.state.kami, r2Base })` and re-scan via `scanBaseParts()` after KAMI init.
3. Remove `three`, `@pixiv/three-vrm`, `@types/three` from `package.json` unless the app uses them for non-avatar purposes (e.g. a three-based 3D editor panel).
4. Verify in-browser: console should show `[kami-web] backend=WebGpu` + `VRM skin state: N joints, M skinned meshes, K spring chains, C node constraints`. Zero fetches to `three` / `@pixiv/three-vrm`.

### Follow-up work

1. **Wgpu-native preset swap** — `kami_vrm::compose` already merges parts and produces GLB bytes. The missing link is:
   - Fetch + parse preset GLB in the browser (via `kami_vrm::parse_vrm` in wasm, or a new `fetch_and_compose` wasm export).
   - Produce recomposed GLB bytes + call `runEmbedVrm` with a blob URL (or a new `reload_vrm_from_bytes` export to avoid re-init).
   - Preserve spring / constraint state across reloads (skeletons should be rebuilt; physics state resets).
2. **Drop `state.three` field** from `DualEngineState` in the next SDK minor version after all consumers are audited.
3. **Retire `createPartComposer`'s three imports entirely** once (1) ships. Then drop `peerDependenciesMeta`.
4. **Yoro / isekai / sabiotoshi audits** — confirm each either already uses `engines: ['kami']` or has a scheduled migration. Track in `deps.toml [[migrations]]`.
5. **ADR-0031 retirement** — when (1)-(4) complete, supersede this ADR with a "three.js no longer a soft dep" follow-up (move to status: superseded).

## References

- VRMC_springBone-1.0 spec: https://github.com/vrm-c/vrm-specification/tree/master/specifications/VRMC_springBone-1.0
- VRMC_node_constraint-1.0 spec: https://github.com/vrm-c/vrm-specification/tree/master/specifications/VRMC_node_constraint-1.0
- `40-engine/kami-engine/CLAUDE.md` §wgpu 統一レンダラ, §Prohibitions, §Ownership & Authority
- `40-engine/kami-engine/ARCHITECTURE.md`
- Runtime verification log: 2026-04-18 baminiku dev server, VRM1_Constraint_Twist_Sample.vrm, 83 joints / 13 skinned meshes / 57 morph targets / 22 spring chains / 14 node constraints, zero WebGPU validation errors, zero three/@pixiv module fetches.
- **L10 locomotion (2026-04-20)**: additive extension inside `run_embed_vrm` — WASD walk / Shift+WASD run / Space jump / third-person orbit camera + idle·walk·run·air pose state machine. Authored as Euler-degree bone tuples (VRM 1.0 humanoid names: `leftUpperLeg` / `rightUpperArm` / `spine` / `chest` / `head`) converted to quaternions and written to `VRM_SKIN_STATE.pose_overrides` per-frame; existing spring/constraint solver consumes overrides unchanged. Root TRS composed into each batch `instance_buffer` via `from_translation * from_rotation_y * base_transform`. Exposed at `isekai.etzhayyim.com/v3-demos.htm#scene=12`. Sanctioned by "VRM viewer surface" carveout; does not introduce new `run_with_*` exports.
