---
id: adr-2605141200-mangaka-3d-scene-pregel-kami-sdk
title: "mangaka 3D scene composition — Pregel graph + kami-mangaka-scene SDK"
status: proposed
doc_type: adr
topic: mangaka-3d-scene-pregel
authoritative: true
last_verified: 2026-05-14
authoritative_for:
  - mangaka 3D scene composition pipeline (character → 3D model → background/camera/object placement → simulation → render)
  - kami-mangaka-scene Rust crate (engine-side facade above kami-vrm / kami-scene-graph / kami-render / kami-postfx / kami-dec / kami-pipelines)
  - LangGraph Pregel `compose_scene_3d` graph wired into lg_mangaka
  - XRPC procedure `com.etzhayyim.mangaka.composeScene3d`
priority: 7.2
axis: generation-pipeline
weight: 0.72
priority_note: "Activates the 3D-proxy path deferred by ADR-0057 once the ghost-hacker character set stabilises. Coexists with current 2D M2+ref pipeline (`lg-image-gen`)."
depends_on:
  - adr-2605080600-langgraph-server-granian-l3-runtime
  - adr-2605082000-langgraph-graph-definition-as-data
  - adr-2605082100-langgraph-checkpointer-storage
  - adr-2605082200-pyzeebe-handler-thin-dispatcher-contract
  - adr-2605111200-cf-worker-edge-only-no-rw-connection
related:
  - adr-0057-manga-bpmn-actor-pipeline
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
  - adr-0036-three-tier-write
supersedes: []
superseded_by: []
notes: |
  User directive 2026-05-14: "mangaka のシーン設計に 3d model を使って、
  シーンを設計する pregel を設計. キャラクターから 3d model を整形して、
  3d で背景、カメラ、object などを配置、また 3d シュミレーションを使って
  演算. kami engine sdk を統合、また sdk を設計して。"
  ADR-0057 (2026-03 manga BPMN pipeline) deferred 3D-proxy until the
  character set stabilised; ghost-hacker series import (data/ghosthacker/
  2026-05-12) plus 14 LangGraph-driven character / environment vertices
  in production satisfy that gate.
---

# Context

## Current state (2026-05-14)

mangaka.etzhayyim.com panel generation runs entirely on **2D diffusion**:

| Stage | Location | Tech |
|---|---|---|
| Plan | `60-apps/etzhayyim-project-mangaka/lg-image-gen/src/phase3-4-semantic-panels.ts` | gpt-4o semantic decomposition |
| Generate | `lg-image-gen/src/lib/openai.ts` | gpt-image-2 / Gemini 3 Pro Image, 832×1216 monochrome |
| Critique | `lg-image-gen/src/graph-m2.ts` | gpt-4o-mini-vision 7-axis scoring |
| Refine | conditional, max 3 iter when `Q_total < 0.75` | LLM reprompt |
| Persist | `lg-image-gen/src/run.ts` | PNG versioning + `episode.jsonld` |

LangGraph Server is live for mangaka: FastAPI + Pregel idiom across 7
graphs (`analyze_character_graph.py:27`, `enrich_characters.py`,
`enrich_environments.py`, `derive_chapter_incidents.py`,
`backfill_mangaka_edges.py:7`, `enrich_organizations.py`,
`import_chat_history.py`). Granian L3 (ADR-2605080600) and
graph-as-data YAML (ADR-2605082000 Phase B/C) are not yet active; the
mangaka deployment uses FastAPI directly with a Python `StateGraph`.

ADR-0057 §"Method 3 — 3D-proxy 再評価" deferred 3D character composition
until the character roster stabilised, with the explicit gate that 第2
話以降で character set が固定化したら 3D-proxy を再検討 (initial 3D
modeling コストを連載で amortize)。The ghost-hacker import (2026-05-12,
14 character vertices, 4 environment vertices, 1 organisation vertex)
satisfies that gate.

## KAMI engine assets already in tree

| Crate | Function | Path |
|---|---|---|
| `kami-scene-graph` | DAG + `LocalTransform`/`WorldTransform`/`Parent`/`Children`, hecs integration | `40-engine/kami-engine/kami-scene-graph/src/lib.rs` |
| `kami-vrm` | VRM 1.0 parse/decompose/compose/export + spring-bone verlet + Aim/Rotation/Roll constraint solver | `40-engine/kami-engine/kami-vrm/` |
| `kami-skeleton` | Bone hierarchy + GPU skinning + blend trees | `40-engine/kami-engine/kami-skeleton/` |
| `kami-gltf` | glTF 2.0 loader | `40-engine/kami-engine/kami-gltf/` |
| `kami-render` | wgpu unified PBR renderer (Backends::BROWSER_WEBGPU | GL, Metal, Vulkan, DX12) | `40-engine/kami-engine/kami-render/` |
| `kami-postfx` | Outline / vignette / pixelate / CRT — basis for manga inking pass | `40-engine/kami-engine/kami-postfx/` |
| `kami-pipelines` | `SkyAdapter` / `TerrainAdapter` / `WaterAdapter` / `ParticleAdapter` / `GsplatAdapter` (3D Gaussian splat WGSL EWA) | `40-engine/kami-engine/kami-pipelines/` |
| `kami-terrain` / `kami-atmosphere` / `kami-vegetation` | Background biome + sky + wind field | `40-engine/kami-engine/kami-{terrain,atmosphere,vegetation}/` |
| `kami-dec` | DEC physics (heat / wind / water / Maxwell EM) on cubical complex | `40-engine/kami-engine/kami-dec/` |
| `kami-app` | Builder facade (`KamiApp::new_web/.with_*/.run`, `RenderPipeline` trait, `Camera`, `DepthTarget`) | `40-engine/kami-engine/kami-app/` |

The engine has everything needed for headless 3D scene composition.
What is missing is (a) a mangaka-oriented facade that composes these
crates with manga grammar (shot type / 3-point lighting / outline pass
/ tone) and (b) the LangGraph orchestration node that drives the
facade from the existing 7-graph Pregel pipeline.

# Decision

Add a new **Pregel super-step graph** `compose_scene_3d` to
`lg_mangaka`, backed by a new **`kami-mangaka-scene` Rust crate** that
provides the headless render facade. The facade is exposed to LangGraph
nodes through PyO3 bindings (server side, pod runtime) and to the
appview Genko canvas through wasm-pack (browser preview).

## 1. Pregel graph (LangGraph StateGraph compiled to BSP)

Module: `60-apps/etzhayyim-project-mangaka/lg/lg_mangaka/graphs/compose_scene_3d.py`
Registered in `lg/langgraph.json` as `compose_scene_3d`.

9 super-steps (each a node; LangGraph applies an implicit barrier
between consecutive nodes per ADR-2605131600 §2):

| # | Node | Inputs (read channels) | Outputs (write channels) | Side-effects |
|---|---|---|---|---|
| 1 | `load_panel_plan` | `panel_rkey`, `refine_from_rkey?` | `panel_plan` | SELECT `vertex_mangaka kind='panel'` |
| 2 | `resolve_assets` | `panel_plan` | `asset_refs` | SELECT character / environment / asset vertex; resolve VRM/glTF `blob_key` |
| 3 | `pose_characters` | `panel_plan`, `asset_refs` | `pose_plan` | LLM (gpt-4o) → bone rotations + ARKit expression weights, per character |
| 4 | `place_scene` | `pose_plan`, `asset_refs`, `panel_plan` | `scene_dag` | Build `kami-scene-graph` DAG (ground + sky + props + characters with `WorldTransform`); spawn anchors from `environment.layout` |
| 5 | `cinematography` | `scene_dag`, `panel_plan.mood` | `camera_plan` | LLM → camera (eye, target, fov, roll, DoF) + 3-point lighting (key/fill/rim) with manga grammar (FullShot / MediumShot / Closeup / OverShoulder / Dutch) |
| 6 | `simulate` | `scene_dag`, `camera_plan` | `sim_result` | kami-vrm spring-bone settle (~30 ticks) + cloth verlet + optional particles + DEC wind/dust if `env.weather` set; **fan-out via `Send` per character for parallel spring-bone solve** |
| 7 | `render_keyframes` | `sim_result`, `camera_plan` | `renders[]` | Headless `kami-mangaka-scene::render_multi(angles)` → PNG (base+depth+outline+toon), 1 main + ±2 alt angles, content-addressed B2 upload |
| 8 | `critique_and_select` | `renders[]`, `panel_plan` | `selected`, `score` | gpt-4o-mini-vision 7-axis (composition, silhouette, character recognisability, framing, manga grammar, lighting drama, action clarity) → best pick; **conditional edge: `score<0.75 ∧ iter<3 → cinematography`** |
| 9 | `persist` | `selected`, `panel_plan` | `status`, `scene_rkey` | INSERT `vertex_mangaka_scene_3d` via asyncpg (k8s pod side, NOT CF Worker — see ADR-2605111200); optional `com.etzhayyim.mangaka.generatedImage` record |

`Send`-based parallel fan-out from step 6 to per-character spring-bone
solvers requires the canonical shallow-dict reducer
(ADR-2605131600 §2):

```python
def _merge_dict(a, b):
    if not a: return dict(b or {})
    if not b: return dict(a)
    out = dict(a); out.update(b); return out

class _State(TypedDict, total=False):
    sim_result: Annotated[Dict[str, Any], _merge_dict]
```

## 2. `kami-mangaka-scene` Rust crate

Location: `40-engine/kami-engine/kami-mangaka-scene/`
Workspace member of `40-engine/kami-engine/Cargo.toml`.

Crate dependencies (engine-internal only — no new third-party):

```
kami-mangaka-scene
  ├── kami-scene-graph
  ├── kami-vrm
  ├── kami-skeleton
  ├── kami-gltf
  ├── kami-terrain
  ├── kami-atmosphere
  ├── kami-render
  ├── kami-postfx
  ├── kami-pipelines
  ├── kami-dec (optional, feature-gated `sim-dec`)
  └── kami-app
```

The engine is not modified; this crate is a thin facade.

Public API (Rust):

```rust
pub struct MangakaScene { /* hecs::World + kami-scene-graph root */ }

impl MangakaScene {
    pub fn new() -> Self;

    // 1. Character (3D model 整形)
    pub fn load_character(&mut self, vrm: &[u8], rkey: &str) -> CharacterId;
    pub fn pose(&mut self, c: CharacterId, pose: &PoseSpec);
    pub fn expression(&mut self, c: CharacterId, emo: Expression);

    // 2. Background / props
    pub fn set_background(&mut self, env: &EnvironmentSpec);
    pub fn add_prop(&mut self, gltf: &[u8], xform: Transform) -> PropId;

    // 3. Camera & lighting
    pub fn set_camera(&mut self, cam: CameraSpec);
    pub fn add_light(&mut self, light: LightSpec);

    // 4. Simulation
    pub fn tick(&mut self, dt: f32);
    pub fn settle(&mut self, ticks: u32);
    pub fn add_wind(&mut self, dir: Vec3, speed: f32);
    pub fn add_particle_burst(&mut self, kind: FxKind, at: Vec3);

    // 5. Render
    pub fn render(&self, opts: RenderOpts) -> RenderResult;
    pub fn render_multi(&self, angles: &[CameraSpec]) -> Vec<RenderResult>;

    // 6. Round-trip
    pub fn to_jsonld(&self) -> serde_json::Value;
    pub fn from_jsonld(v: &serde_json::Value) -> Result<Self, SceneError>;
}
```

`ShotGrammar` enum is the manga vocabulary (FullShot / MediumShot /
Closeup / OverShoulder / Dutch / BirdsEye / WormsEye); it is 1:1 with
the semantic-panel schema in
`60-apps/etzhayyim-project-mangaka/lg-image-gen/src/phase3-4-semantic-panels.ts`.

PyO3 bindings expose the same surface as `kami_mangaka_scene` Python
module, built via `maturin` into the LangGraph pod image. wasm-pack
target=web builds a browser bundle consumed by
`appview/etzhayyim-wasm-mangaka-mng4k4x1/svelte/static/` for editor
preview, per the per-game WASM pattern in `60-apps/CLAUDE.md`.

## 3. Persistence (ADR-2605111200 compliant)

CF Worker (`60-apps/etzhayyim-project-mangaka/appview/etzhayyim-wasm-mangaka-mng4k4x1/src/app.ts`)
is **edge-only**. It accepts the XRPC procedure and forwards to
bpmn-dispatcher → LangGraph Server. Kotoba/Datomic writes happen in the
LangGraph pod via asyncpg.

New table (timestamp-based Alembic migration):

```sql
CREATE TABLE vertex_mangaka_scene_3d (
  vertex_id        varchar PRIMARY KEY,
  _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
  rkey             varchar NOT NULL,
  work_id          varchar,
  chapter_id       varchar,
  page_id          varchar,
  panel_id         varchar NOT NULL,
  scene_jsonld     varchar,           -- kami-mangaka-scene::to_jsonld output
  camera_jsonld    varchar,
  render_blob_key  varchar,           -- sha256 hex, B2 content-addressed
  depth_blob_key   varchar,
  outline_blob_key varchar,
  score            double precision,
  iteration        int,
  sim_seed         bigint,
  created_at       varchar NOT NULL,
  actor_did        varchar NOT NULL,
  org_did          varchar NOT NULL,
  at_did           varchar
);
CREATE INDEX idx_mangaka_scene_3d_panel ON vertex_mangaka_scene_3d (panel_id);
CREATE INDEX idx_mangaka_scene_3d_work  ON vertex_mangaka_scene_3d (work_id, chapter_id);
```

Image blobs reuse the existing content-addressed PDS layout
(`blobs/{repo}/{sha256hex}`) so identical renders dedupe across
iterations.

## 4. XRPC contract

`00-contracts/lexicons/com/etzhayyim/apps/mangaka/composeScene3d.json`:

```
com.etzhayyim.mangaka.composeScene3d  (procedure)
  input:  { panelRkey: string, refineFromRkey?: string, maxIter?: integer(1..5) }
  output: { sceneRkey: string,
            renders: [{ blobKey, score, angle }],
            iterations: integer,
            tookMs: integer }
```

Worker flow (Tier 2 domain — but **without** local INSERT per
ADR-2605111200):

```
appview Worker (src/app.ts)
   └─ sdk.app.command("com.etzhayyim.mangaka.composeScene3d", h)
       └─ bpmn-dispatcher
           └─ LangGraph Server `/runs/compose_scene_3d`
               └─ pod: asyncpg → INSERT vertex_mangaka_scene_3d
                   + B2 PUT blobs/{repo}/{sha256}
```

## 5. Coexistence with current 2D pipeline

`lg-image-gen` (TypeScript LangGraph, M2+ref) remains active. A new
hybrid mode `m3-hybrid` is added to `lg-image-gen/src/graph-m3.ts`:
the `compose_scene_3d` PNG (base + outline + depth) is supplied as
reference image to gpt-image-2 / Gemini 3 Pro Image. The Pregel critique
step compares M2 vs M3 by η-score (7-axis sum) and selects the winner.
ADR-0057's prediction is that M3 wins as the character set amortises.

# Consequences

| | |
|---|---|
| **+** | Activates ADR-0057 deferred 3D-proxy path. Manga shot grammar becomes declarative (`ShotGrammar` enum) instead of free-form LLM prompt. |
| **+** | Re-uses 100% of existing kami crates. Zero net-new engine code outside the facade. |
| **+** | LangGraph `Send` fan-out gives near-linear spring-bone settle across N characters. |
| **+** | Same scene `jsonld` round-trips between server (pod) and browser preview (wasm-pack) — editor sees what the renderer rendered. |
| **−** | Adds a new VRM/glTF asset dependency for each character. Bootstrap cost is amortised by ADR-0057's stabilisation gate. |
| **−** | Pod image grows by the maturin-built `kami_mangaka_scene` wheel + wgpu native lib (~30–50 MB). Mitigation: pod has GPU node selector via murakumo VKE (ADR-2605122100). |
| **−** | New migration `vertex_mangaka_scene_3d` adds one base table + 2 indexes. Trivial under the multi-head Alembic workaround (psycopg phased apply per `30-graph/graph-schema/CLAUDE.md`). |

# Alternatives considered

## A. Run kami-mangaka-scene inside the CF Worker (WASM)

Pros: keeps everything at the edge. Cons: 30s/128 MB CPU budget, no
GPU, no asyncpg path under ADR-2605111200. **Rejected** — render must
live on a pod.

## B. Build a separate Python 3D renderer (PyBullet / Blender headless)

Pros: avoids new Rust crate. Cons: 2nd 3D stack in tree, duplicates
kami-engine investment, no parity with the live preview the editor
sees. **Rejected**.

## C. Defer 3D until the full Granian L3 + graph-as-data migration

Pros: cleaner ADR sequencing. Cons: blocks the user's explicit
directive and ADR-0057's amortisation argument by an unbounded amount.
**Rejected** — the new graph is written in the same Python `StateGraph`
idiom as the other 7 mangaka graphs and migrates with them when phase
B/C lands.

## D. Re-author the BPMN flow under ADR-0057 with 3D activities

Pros: ADR-0057 consistency. Cons: contradicts ADR-2605131600
(LangGraph is canonical for new orchestrations). **Rejected**.

# Roadmap

| Phase | Scope | Days |
|---|---|---|
| P0 | `kami-mangaka-scene` crate skeleton + headless wgpu render (1 character, 1 cam, no sim) | 2 |
| P1 | VRM load + pose lexicon + spring-bone settle | 2 |
| P2 | Background (kami-terrain biome preset) + 3-point lighting + outline postfx | 2 |
| P3 | LangGraph `compose_scene_3d` Pregel (9 steps) + lexicon + Worker XRPC | 3 |
| P4 | Critique loop (gpt-4o-mini-vision) + B2 persist + migration | 2 |
| P5 | wasm-pack facade for appview interactive preview | 3 |
| P6 | Graph-as-data YAML migration + Granian L3 (per ADRs 2605080600 / 2605082000) | 3 |

Total ≈ 17 working days. P0–P3 yield the end-to-end pipe; P4–P5 close
the editor loop; P6 brings the graph into ADR alignment.

# References

- ADR-0057 `manga-bpmn-actor-pipeline` — original 2D pipeline; defers 3D-proxy to series 2+
- ADR-2605080600 `langgraph-server-granian-l3-runtime`
- ADR-2605082000 `langgraph-graph-definition-as-data`
- ADR-2605082100 `langgraph-checkpointer-storage`
- ADR-2605082200 `pyzeebe-handler-thin-dispatcher-contract`
- ADR-2605111200 `cf-worker-edge-only-no-rw-connection`
- ADR-2605131600 `malak-orchestration-langgraph-pregel-langserve` — reference for Pregel `Send` reducer
- `60-apps/etzhayyim-project-mangaka/CLAUDE.md` §KAMI Engine Integration
- `60-apps/CLAUDE.md` §Per-Game WASM Pattern (per-app crate convention)
- `40-engine/kami-engine/CLAUDE.md` (crate inventory)
