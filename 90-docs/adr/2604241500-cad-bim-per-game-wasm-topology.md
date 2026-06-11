---
id: adr-2604241500-cad-bim-per-game-wasm-topology
title: "ADR: CAD / BIM adopt per-game WASM topology; container reduced to heavy job service"
status: proposed
doc_type: adr
topic: cad-bim-runtime
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - cad.etzhayyim.com viewer runtime
  - bim.etzhayyim.com viewer runtime
  - kami-app-{cad,bim} / kami-bim / kami-cad responsibility split
related:
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0002-graph-storage-appview
  - 260320-kotodama-cloudflare-containers-evaluation
supersedes: []
superseded_by: []
---

# Context

`60-apps/etzhayyim-project-cad/260320-cad-kotodamaapp-design.md` (2026-03-20) が
CAD app を **Container runtime + Threlte viewer** 前提で設計している。

一方で 2026-04 に `60-apps/CLAUDE.md` が CRITICAL ルールとして
「新しい WebGPU / 3D 体験は `kami-app-{game}` 独立 crate で作る。
`kami-web::run_with_*` 追加禁止」を定めた (ARCHITECTURE.md §Migration)。

kami-engine 側の素材:

- `kami-cad` crate が既に存在 (BREP topology + 解析 surface/curve +
  parametric feature tree + assembly, f64 精度)
- `kami-sdf` / `kami-mesher` / `kami-gltf` / `kami-scad` が CAD に必要な
  生成・出力スタックを提供
- `@etzhayyim/kami-engine-sdk` (TS/Svelte) が WASM ラッパーとして存在
- `kami-app` Builder SDK + `kami-pipelines` shared adapter (Sky/Terrain/
  Water/Voxel/Particle) が整備済

同時に `bim.etzhayyim.com` は未作成で、IFC native のドメインモデルが
`30-graph` にも `40-engine` にも存在しない。

現状をそのまま放置すると以下の不整合が固定化する:

1. CAD viewer path が container cold-start (数秒〜十数秒) を必ず通り、
   browser 側 edge 体験が悪化
2. 同じ BREP/tessellation コードを container + kami-cad に二重持ち
3. bim は CAD と別 runtime (Threlte 直描画 or container 独自) に
   流れる可能性があり、両者で共有できる adapter/pipeline が育たない
4. per-game WASM ルールの CRITICAL 宣言と CAD 既存設計が矛盾したまま

# Decision

`cad.etzhayyim.com` と `bim.etzhayyim.com` は **per-game WASM topology** を DEFAULT
とする。container runtime は「STEP/IGES/IFC parse、tessellation、
rebuild、図面 export など、Worker の CPU/memory 制約では無理な処理」
に限定した **heavy job service** (`cad-job.etzhayyim.com` / `bim-job.etzhayyim.com`)
に縮退する。viewer hot path は Worker 1 経路で完結させる。

## Topology (CAD / BIM 共通形)

```
┌─ L4 game crate ───────────────────────────────────────────────┐
│ kami-app-cad  →  run_cad_v2(canvas_id)                          │
│ kami-app-bim  →  run_bim_v2(canvas_id)                          │
│  ~50 LoC 合成のみ (camera / input / pipeline choice)            │
└───────────┬─────────────────────────────────────────────────────┘
            │
┌─ L3 domain kernel + shared pipelines ─────────────────────────┐
│ kami-cad  (BREP, feature tree, assembly)                        │
│ kami-bim  (IFC: project/site/building/storey/space/element,     │
│            pset/classification/quantities)                      │
│ kami-pipelines::CadSceneAdapter / BimSceneAdapter (forthcoming) │
└───────────┬─────────────────────────────────────────────────────┘
            │
┌─ L2 kami-app Builder SDK ───────────────────────────────────────┐
│ Camera / Input / RAF / DepthTarget / HUD publish                │
└───────────┬─────────────────────────────────────────────────────┘
            │
┌─ L1 kami-render (GPU bootstrap, pipelines, shaders) ────────────┐
└─────────────────────────────────────────────────────────────────┘

Off-path:  cad-job.etzhayyim.com / bim-job.etzhayyim.com (CF Container, standard-1 4 GiB)
  ├─ STEP / IGES / IFC parse (ifcopenshell + trimesh; OCP for STEP/IGES Phase 2.5)
  ├─ Tessellation caches (→ B2 content-addressed, ADR-0048)
  ├─ Rebuild / boolean / section
  └─ IFC / glTF / PDF / DXF / BCF / xlsx export
```

## App Worker 契約

| 項目 | CAD | BIM |
|---|---|---|
| Primary handle | `cad.etzhayyim.com` | `bim.etzhayyim.com` |
| Primary DID | `did:web:cad.etzhayyim.com` → `did:plc:cad` (Phase 5) | `did:web:bim.etzhayyim.com` → `did:plc:bim` |
| Nanoid | `cd4dview` (既存) | `b1m3d1tr` (新規) |
| Runtime | `worker` (TS Native + `@etzhayyim/kotodama-host-sdk`) | `worker` |
| Lexicon root | `com.etzhayyim.apps.cad.*` | `com.etzhayyim.apps.bim.*` |
| Persistence | Hyperdrive direct (ADR-0036) on `vertex_cad_*` | Hyperdrive direct on `vertex_bim_*` |
| Blob storage (ADR-0048) | B2 (Backblaze B2) SHA-256 content-addressed (`etzhayyim-cad/cad/{blobs,meshes,exports}/{sha}`) | B2 同上 (`etzhayyim-bim/bim/{blobs,meshes,exports}/{sha}`) |
| Social derive | revision publish / comment resolve → `app.bsky.feed.post` | 同左 (annotation resolve, revision publish) |

## Phase 1 CAD lexicons (SSoT: `00-contracts/lexicons/com/etzhayyim/cad/`)

| NSID | type |
|---|---|
| `com.etzhayyim.apps.cad.importCadFile` | procedure |
| `com.etzhayyim.apps.cad.getRevisionScene` | query |
| `com.etzhayyim.apps.cad.addAnchoredComment` | procedure |
| `com.etzhayyim.apps.cad.listComments` | query |
| `com.etzhayyim.apps.cad.requestExport` | procedure |

## Phase 1 BIM lexicons (SSoT: `00-contracts/lexicons/com/etzhayyim/bim/`)

| NSID | type |
|---|---|
| `com.etzhayyim.apps.bim.importIfc` | procedure |
| `com.etzhayyim.apps.bim.getStoreyScene` | query |
| `com.etzhayyim.apps.bim.listSpaces` | query |
| `com.etzhayyim.apps.bim.annotateElement` | procedure |
| `com.etzhayyim.apps.bim.requestExport` | procedure |

## Workspace 追加

- `40-engine/kami-engine/kami-bim/` (新規 crate、IFC-like model)
- `40-engine/kami-engine/kami-app-cad/` (新規 crate、`run_cad_v2`)
- `40-engine/kami-engine/kami-app-bim/` (新規 crate、`run_bim_v2`)
- `60-apps/etzhayyim-project-bim/` (新規 project scaffold)

`40-engine/kami-engine/Cargo.toml` workspace members に上記 3 crate を追加。

# Consequences

## 良い影響

- Viewer hot path が Worker + per-game wasm (180–220 KB) で edge 配信、
  container cold-start を踏まない
- CAD / BIM が同じ Builder SDK / RenderPipeline 契約を共有し、
  `CadSceneAdapter` / `BimSceneAdapter` の開発コストが 1 回で済む
- 新しい viewer 機能 (section plane, explode, storey LOD) を追加する
  blast radius が **per-game crate の 1 ファイル** に閉じる
- kami-bim が IFC の in-memory モデルを正規化し、graph schema / job
  service / Worker / CLI が同一型定義を共有できる
- per-game WASM CRITICAL ルールと CAD/BIM 実装方針が一致

## コスト・リスク

- 重い処理 (STEP/IGES/IFC parse、boolean、PDF/DXF export、BCF) のために
  container を 2 つ維持する必要あり。viewer 1 経路 + job 2 経路 = 合計 3
  経路の運用
- `CadSceneAdapter` / `BimSceneAdapter` + BREP→mesh streaming + IFC
  hierarchical LOD は未実装。Phase 1 の `run_cad_v2` / `run_bim_v2` は
  Sky のみ描画する bootstrap scaffold
- OpenCascade 等の大型 C++ kernel を使いたい場合は job service 側でのみ
  採用可。Viewer にロードできない (wasm bundle 制約)

## 禁止事項

- `kami-web::run_with_*` に cad / bim エントリを追加してはならない
- `com.etzhayyim.apps.{cad,bim}.*` domain collection を `sdk.pds.createRecord`
  で書いてはならない (ADR-0036、Hyperdrive 直接)
- IFC STEP や STEP203 の raw text を AT Record (federable) に埋めては
  ならない (`blobKey` 参照のみ)
- 図面レビュー以外のフル authoring (MEP 設計、構造解析、施工管理、CAM
  toolpath 生成) は Phase 1 scope 外。Phase 2 で個別 ADR を切る

## Migration status

| 項目 | 状態 |
|---|---|
| 260320-cad-kotodamaapp-design.md | Container 前提 → 本 ADR で **per-game WASM DEFAULT に修正**、container は job service に降格 |
| `kami-cad` crate | 既存。変更なし (BREP + feature tree + assembly) |
| `kami-bim` crate | **新規作成** (本 ADR で着地) |
| `kami-app-cad` | **新規作成** (Phase 1 は Sky のみ scaffold、BREP scene adapter は続 PR) |
| `kami-app-bim` | **新規作成** (Phase 1 は Sky のみ scaffold、BIM scene adapter は続 PR) |
| `60-apps/etzhayyim-project-bim` | **新規作成** (Worker + lexicons + CLAUDE.md) |
| `60-apps/etzhayyim-project-cad` CLAUDE.md | runtime 記述を `container` → `worker (viewer) + container (job)` に更新 (本 ADR 反映の follow-up) |

# Alternatives Considered

## A. Container 一本 (既存 260320 方針を維持)

- pro: OpenCascade など native CAD kernel を自由に使える。1 経路で完結
- con: per-game WASM CRITICAL 違反、container cold-start が毎 viewer 起動に乗る、
  kami-engine エコシステム (Builder SDK / shared pipelines) から切り離される

## B. Threlte (three.js) 直描画、WASM 不使用

- pro: 既存 260320 前提のまま、Svelte と自然統合
- con: BREP 処理を JS/TS で再実装する必要 or container 経由で強制される、
  `kami-cad` / `kami-bim` Rust カーネルが viewer 側で使えない、per-game
  WASM CRITICAL 違反

## C. 採用案 = per-game WASM (viewer) + container (heavy job) 2 層

- pro: CRITICAL 準拠、edge 配信、shared adapter 再利用、重い処理は
  container で自由に native 依存可
- con: 運用経路が viewer + job で 2 経路、最初の BIM scene adapter 実装
  コストが発生

採用: **C**。CRITICAL ルールとの整合、kami-engine 投資の再利用、
viewer UX (cold start ゼロ) を優先。

# References

- `60-apps/CLAUDE.md` §Per-Game WASM Pattern (CRITICAL, 2026-04)
- `40-engine/kami-engine/ARCHITECTURE.md`
- `60-apps/etzhayyim-project-cad/260320-cad-kotodamaapp-design.md`
- ADR-0036 (Worker-direct Hyperdrive)
- ADR-0002 (Graph storage / AppView)
- IFC 4.3 schema: https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/
- BCF 3.0 API: https://buildingsmart-community.github.io/BCF/
