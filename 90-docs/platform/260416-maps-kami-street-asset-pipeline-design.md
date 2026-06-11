---
id: maps-kami-street-asset-pipeline
title: Maps to KAMI Street Asset Pipeline Design
status: active
doc_type: reference
topic: maps-kami-runtime
authoritative: true
last_verified: 2026-04-17
authoritative_for:
  - maps.etzhayyim.com street-level spatial asset pipeline
  - KAMI runtime format for photogrammetry-derived city assets
  - Mapillary-derived reconstruction policy
related:
  - maps-vision-satellite-pipeline
  - 260409-unified-access-control-shannon-design
supersedes: []
superseded_by: []
---

# Maps to KAMI Street Asset Pipeline Design

`maps.etzhayyim.com` で収集した street-level imagery を、`kami engine` で実行可能な軽量 3D アセットへ落とすための設計。結論は明確で、**NeRF / 3DGS は再構成用の中間表現としてのみ使い、ランタイム配信形式には採用しない**。

## Goal

- Mapillary 由来の画像から、ゲーム実行に耐える街区 3D アセットを生成する
- `maps.etzhayyim.com` の graph-first / DID-scoped source 設計を崩さずに provenance を保持する
- `kami engine` の wgpu + Rust WASM ランタイムに適した形式へ焼き込む
- Switch クラスを含む resource-constrained device で成立するメモリ・I/O・描画予算に収める

## Decision

### Final Runtime Format

最終成果物は以下に固定する。

- **static mesh 主体**
- **baked textures / baked normals / baked AO**
- **LoD 階層**
- **instancing 可能な prop catalog**
- **glTF/GLB + meshopt + KTX2/BasisU**

NeRF / 3D Gaussian Splatting は以下に限定する。

- 局所高品質再構成
- 深度補完や欠損補修
- mesh bake 前の見た目改善

### Non-Goals

以下は採用しない。

- city-scale 3DGS をそのまま配信する構成
- Mapillary 全画像を丸ごと ingest する構成
- photogrammetry mesh を無加工でゲームに入れる構成
- object ごとに独立マテリアルと独立テクスチャを持つ構成

## System Boundary

### maps.etzhayyim.com の責務

- 画像・シーケンス・bbox 単位の収集制御
- `did:web:maps.etzhayyim.com:street_view` による provenance 管理
- Collection Job 発行
- graph 上での Spot / Route / Building / VisionResult との紐付け
- 画像から意味表現への抽象化

### KAMI Engine の責務

- 軽量化済みメッシュの描画
- LoD 切り替え
- occlusion / frustum / distance culling
- instanced prop 描画
- tile / chunk 単位の streaming
- gameplay 用 collision / nav / interaction surface の保持

## Architecture Overview

```text
Mapillary / street_view sequence
  -> frame selection
  -> SfM / SLAM camera solve
  -> sparse geometry + semantic labels
  -> depth completion / local MVS
  -> optional local NeRF or 3DGS refinement
  -> mesh reconstruction
  -> semantic re-parameterization
  -> atlas bake + LoD build + compression
  -> KAMI runtime package
```

## Pipeline

### 1. Acquisition and Selection

`maps.etzhayyim.com` は Mapillary 画像を全件保持しない。取得は bbox / sequence / landmark priority ベースで行い、隣接フレームの高重複区間を先に落とす。

選別ルール:

- 直進連続フレームは視差閾値で間引く
- 交差点、曲がり角、ランドマーク前後は高密度保持
- 動体・露出崩れ・ブレの強いフレームは除外
- 再構成不能なシーケンスは graph 上で失敗理由を保存

この段階で 70-95% を削る前提にする。

### 2. Geometric Backbone

幾何の基礎は SfM / SLAM で作る。Neural reconstruction を最初の骨格にはしない。

出力:

- camera pose
- sparse point cloud
- reconstruction confidence
- track coverage per segment

この結果を `maps.etzhayyim.com` では collection artifact として管理し、街区ごとの asset build job に渡す。

### 3. Depth and Local Refinement

欠損の大きい領域にだけ depth completion / MVS を適用する。さらに必要なら局所的に NeRF / 3DGS を使う。

対象は限定する。

- 主要交差点
- プレイヤー導線の近景
- ランドマーク
- mesh 化で破綻しやすい複雑な立面

原則は **neural everywhere ではなく neural where it pays**。

### 4. Semantic Re-Parameterization

圧縮率を最大化する中心工程はここで、画像由来の連続表現をゲーム向け意味表現へ置き換える。

変換規則:

- 道路: spline + lane width + curb profile
- 建物: footprint + height bands + facade atlas
- 標識 / 街灯 / ガードレール: instanced props
- 樹木 / 植栽: cards / impostors / low-poly cluster
- 地面: tiled materials + decal overlays

ここで「見た目を壊さずに情報量だけ落とす」。

### 5. Mesh Bake and Compression

最終成果物は mesh 系に bake する。

- static mesh へ統合
- hidden face / duplicate face 除去
- material merge
- texture atlas 化
- LoD0/1/2/3 生成
- mesh quantization
- `EXT_meshopt_compression`
- `KHR_texture_basisu`

### 6. Runtime Packaging

`kami engine` に渡す配信単位は city 全体ではなく chunk 単位にする。

推奨単位:

- `map tile` と整合する街区 chunk
- 近景 mesh pack
- prop catalog
- collision mesh
- nav mesh
- metadata sidecar

metadata sidecar には以下を含める。

- source DID
- sequence ids
- build version
- confidence
- generated_at
- chunk bbox
- LoD budget

## Data Model Integration

`maps.etzhayyim.com` の graph には、実行時アセットそのものではなく build provenance と意味抽象を保持する。

追加または運用強化するエンティティ:

- `CollectionJob` — frame selection / reconstruction / bake / package 各段階
- `VisionResult` — semantic extraction と confidence
- `Building` / `Route` / `Spot` — 実行時に必要な抽象化済み空間要素
- `Asset` — KAMI runtime package 参照
- `SpatialVersion` — chunk 単位の版管理

推奨 edge:

- `ANALYZED_FROM`
- `DERIVED_FROM`
- `PACKAGED_AS`
- `SAME_AS`

## KAMI Runtime Design

### Core Policy

`kami engine` は再構成エンジンではなく、**焼き込み済み city asset の再生系**として扱う。

### Required Runtime Features

- chunk streaming
- hierarchical LoD
- instanced prop renderer
- terrain / road / facade 用 material atlas binding
- CPU 軽量 collision representation
- visibility culling
- async asset decode

### Avoid in Runtime

- dense splat rasterization
- runtime NeRF evaluation
- per-object material explosion
- per-frame heavy LoD search

## Compression Priority

圧縮効果が大きい順に優先する。

1. frame thinning
2. semantic abstraction
3. hidden / duplicate geometry removal
4. instancing
5. atlas reduction
6. mesh simplification + quantization
7. meshopt compression
8. KTX2/BasisU texture compression
9. runtime culling

最適化の主戦場は codec ではなく、**codec 前に何を消すか**である。

## Recommended Build Split

### A. Wide Area

都市全体は semantic-first に作る。

- road network
- building massing
- sidewalk / curb
- utility / street furniture seeds

### B. Near-Field Play Space

プレイヤー導線周辺だけ photogrammetry / depth 補完を使って mesh 化し、ベイク後に配信する。

### C. Hero Zones

見せ場だけ局所的に NeRF / 3DGS を使って reconstruction quality を上げ、その後 mesh bake する。

## Chunk Size Guidance

近景 playable chunk の標準は `50m x 50m` とする。`100m x 100m` は dense urban では少し大きく、draw call、遮蔽、テクスチャ局所性、再ビルド単位のどれも悪化しやすい。

推奨使い分け:

- `25m x 25m`: hero zone、駅前、交差点、ランドマーク周辺
- `50m x 50m`: **標準**。近景の街路体験用
- `100m x 100m`: 郊外、遠景、集約 LoD、再構成結果の publish 単位

### Default Budget: 50m x 50m

| Category | Budget | Notes |
|---|---:|---|
| Compressed runtime package | `<= 6 MB` | 配信単位。GLB + KTX2 + metadata 合計 |
| Collision + nav data | `<= 0.8 MB` | CPU 側 lightweight mesh / nav graph |
| Materials | `<= 10` | atlas 前提 |
| Texture atlases | `<= 3` | `2048²` 基本 |
| Draw calls (near field) | `<= 120` | instancing 前提 |
| LoD0 triangles | `<= 90k` | 近景用 |
| LoD1 triangles | `<= 45k` | 中景用 |
| LoD2 triangles | `<= 15k` | 遠景用 |
| LoD3 triangles | `<= 4k` | impostor 直前 |
| Instanced props | `<= 256` | 標識、街灯、植栽、柵など |

### Aggregate Budget: 100m x 100m

`100m x 100m` を使うなら、近景品質ではなく集約 chunk として扱う。

| Category | Budget |
|---|---:|
| Compressed runtime package | `<= 12 MB` |
| Collision + nav data | `<= 1.5 MB` |
| Materials | `<= 12` |
| Texture atlases | `<= 4` |
| Draw calls (near field) | `<= 180` |
| LoD0 triangles | `<= 180k` |
| LoD1 triangles | `<= 90k` |
| LoD2 triangles | `<= 30k` |
| LoD3 triangles | `<= 8k` |
| Instanced props | `<= 512` |

推奨内訳:

- 建物 massing + facade mesh: `55-65%`
- 道路 / 歩道 / 縁石 / 地面 decal: `15-20%`
- street furniture instanced props: `10-15%`
- collision / nav / metadata: `10-15%`

## Build Stages

`maps.etzhayyim.com` から `kami engine` までの build は、以下の 7 stage に分ける。

1. `sequence_select`
   Mapillary sequence を bbox / route / landmark priority で抽出し、重複フレームを落とす。
2. `pose_solve`
   SfM / SLAM で camera pose と sparse cloud を生成する。
3. `depth_refine`
   欠損箇所だけ MVS / depth completion / local neural refinement を適用する。
4. `semantic_reparam`
   道路・建物・街路設備をゲーム向け意味表現へ変換する。
5. `mesh_bake`
   static mesh 統合、atlas bake、collision / nav 生成を行う。
6. `lod_pack`
   LoD 生成、meshopt、KTX2/BasisU 圧縮、chunk metadata 付与を行う。
7. `publish`
   graph 上に `Asset` / `SpatialVersion` を登録し、KAMI runtime package として公開する。

## Mapillary Sequence to 50m Chunk Rules

標準 chunk は `50m x 50m` とし、Mapillary sequence は画像列そのものではなく、**道路中心線と視点分布を使って chunk に切る**。

### Chunking Principle

- chunk は `EPSG:3857` ベースの正方グリッドで管理する
- 1 chunk の canonical size は `50m x 50m`
- chunk key は `z/x/y#chunk:{cx}:{cy}:50m` 形式を使う
- 近景品質は `50m` chunk 単位で保証し、`100m` は publish 集約単位にのみ使う

### Sequence Ingest Unit

Mapillary から直接 chunk を作らず、まず sequence を ingest 単位として持つ。

sequence ごとに保持する最低情報:

- `sequence_id`
- ordered frame list
- capture timestamps
- camera pose または推定 pose
- frame heading
- GPS confidence
- median frame spacing

### Frame Admission Rules

各 frame は以下を満たした場合のみ chunk 候補に入れる。

- blur / exposure / dynamic object score が閾値内
- 隣接 frame と baseline が近すぎない
- GPS jump が異常でない
- heading が極端に暴れていない

標準閾値:

- 直進区間: `4m - 7m` ごとに 1 frame 採用
- 交差点進入 / 脱出: `2m - 3m` ごとに 1 frame 採用
- 急カーブ / ロータリー / 複雑交差点: `1.5m - 2.5m` ごとに 1 frame 採用

### Chunk Assignment

各採用 frame をその中心位置の `50m` chunk に割り当てる。ただし視野の端で隣接 chunk に効くので、実処理では `1-ring neighbor` にも寄与可能とする。

運用ルール:

- primary chunk: camera center が属する chunk
- secondary chunk: view frustum が 20% 以上重なる隣接 chunk
- 1 frame が書き込める secondary chunk は最大 2 個まで

### Minimum Coverage Requirement

`50m` chunk を build 対象にするには、以下を満たす。

- 採用 frame 数 `>= 24`
- 異なる camera position cluster `>= 3`
- 両方向または交差方向を含む heading coverage `>= 90°`
- chunk 面積のうち可視領域 `>= 55%`

以下の場合は hero / fallback に降格する。

- frame 数は十分だが coverage が狭い
- 片側ファサードしか見えていない
- 動体や駐車車両で道路境界が欠ける

### Hero and Aggregate Escalation

- coverage が非常に高く landmark density が高い場合:
  `50m` chunk 内部を `25m` hero micro-chunk に分割してもよい
- 単独 `50m` chunk では sparse だが周囲 4 chunk を束ねれば成立する場合:
  `100m` aggregate build に回す

### Overlap and Seam Rules

chunk 境界の seams を避けるため、build は表示 chunk より広い bake window を使う。

- logical runtime chunk: `50m x 50m`
- reconstruction window: `70m x 70m`
- bake output: 中央 `50m` を採用し、外周 `10m` は seam stabilization 用にのみ使う

これで境界の facade 切断、道路法線不連続、prop 欠落を減らす。

### Street-Type Heuristics

道路種別で標準運用を変える。

- dense urban street:
  `50m` 標準、交差点だけ `25m` 追加
- boulevard / arterial:
  `50m` 標準、中央分離帯や多車線は secondary chunk を厚めに使う
- suburban road:
  `50m` または `100m aggregate`
- highway / elevated road:
  street photogrammetry 主体にしない。road spline + barrier props 優先

### Failure Fallback

`50m` chunk が Mapillary だけで成立しない場合の降格順:

1. semantic-only chunk
   building massing + road spline + instanced props のみ生成
2. terrain/vector hybrid chunk
   vector tile / DEM / registry 情報を主とし、street texture は薄くする
3. no-photogrammetry publish
   chunk metadata だけ公開し、後続再収集待ちにする

### Collection Job Contract

`CollectionJob` は最低でも以下の stage を持つ。

- `sequence_select`
- `frame_admit`
- `chunk_assign`
- `coverage_score`
- `reconstruct`
- `bake`
- `publish`

各 chunk に対して保存する score:

- `frame_count`
- `coverage_ratio`
- `heading_span_deg`
- `view_cluster_count`
- `occlusion_risk`
- `dynamic_object_risk`
- `recommended_chunk_class` (`25m`, `50m`, `100m`, `semantic-only`)

`maps-collection-control-plane` の `createCollectionJob` / `advanceJob` は、street chunk 用に次のフィールドを持つ。

- `pipelineType`
  - `street_chunk`
  - `poi_import`
  - `satellite_scene`
  - `vision_analysis`
- `stage`
  - `sequence_select`
  - `frame_admit`
  - `chunk_assign`
  - `coverage_score`
  - `reconstruct`
  - `bake`
  - `publish`
- `sequenceId`
- `chunkKey`
- `chunkSizeMeters`
- `bbox`
- `frameCount`
- `coverageRatio`
- `headingSpanDeg`
- `viewClusterCount`
- `occlusionRisk`
- `dynamicObjectRisk`
- `recommendedChunkClass`

2026-04-17 時点の実装状態は次のとおり。

- `createCollectionJob` / `advanceJob` / `getJobStatus` / `listJobs` の Lexicon は更新済みで、`kotodama-host-sdk` と PDS の generated registry に再反映済み
- `MapsJob -> vertex_maps_job` の graph resolver は追加済みで、`30-graph/graph-schema/migrations/20260417020000_vertex_maps_job.ts` も定義済み
- Kotoba/Datomic 側の migration 履歴が `20260415140000_strategy_graph` 欠落で壊れているため、`db:migrate` ではなく `vertex_maps_job` は手動 apply で導入済み
- `maps-collection-control-plane` の read path は `vertex_maps_job` を直読みに切り替え済み

一方で、write path はまだ安定化が必要である。

- `createCollectionJob` / `advanceJob` のレスポンスと Lexicon validation は新契約で通る
- 既存の `vertex_maps_job` row は `listJobs` / `getJobStatus` から読める
- ただし `maps-collection-control-plane` からの `vertex_maps_job` append-write は intermittent で、毎回確実には反映されない

したがって、現時点の canonical view は `vertex_maps_job` だが、運用上は **write hardening 前の partial rollout** として扱う。

### Operational Note

- 現行の `maps-collection-control-plane` は route 競合のため `workers.dev` で暫定 deploy して検証している
- 本番 route へ戻す条件は、`vertex_maps_job` への append-write を安定化し、`maps-ui` への統合可否を再評価すること

### Recommended Default

Mapillary ベースの街路生成では、まず sequence を `50m` chunk へ切り、coverage が十分な場所だけ `25m` に細分化する。`100m` は近景 chunk ではなく、publish 集約または sparse area 用とする。

## Runtime Contract

`com.etzhayyim.apps.maps.kamiConfig` は、単純な `tileUrl` 返却ではなく、KAMI が street chunk package を解釈するための descriptor を返す契約に拡張する。

### Example Payload

```json
{
  "schemaVersion": "etzhayyim.kami.street-chunk.v1",
  "packageKind": "streetChunkRuntimePackage",
  "tileUrl": "https://tiles.maps.etzhayyim.com/v1/{z}/{x}/{y}.pbf",
  "source": "env",
  "targetRuntime": "kami-map",
  "chunking": {
    "chunkSizeMeters": 50,
    "chunkKeyFormat": "z/x/y#chunk",
    "coordinateSystem": "EPSG:3857"
  },
  "formats": {
    "mesh": "model/gltf-binary",
    "texture": "image/ktx2",
    "geometryCompression": "EXT_meshopt_compression",
    "textureCompression": "KHR_texture_basisu",
    "metadata": "application/json"
  },
  "lodPolicy": {
    "levels": 4,
    "switchDistancesMeters": [20, 45, 90],
    "impostorStartMeters": 135
  },
  "budget": {
    "chunkSizeMeters": 50,
    "targetRuntimeClass": "switch-class",
    "maxCompressedBytes": 6000000,
    "maxMaterials": 10,
    "maxAtlasCount": 3,
    "maxDrawCallsNearField": 120,
    "maxTrianglesLod0": 90000,
    "maxTrianglesLod1": 45000,
    "maxTrianglesLod2": 15000,
    "maxTrianglesLod3": 4000,
    "maxPropsInstanced": 256,
    "maxCollisionBytes": 800000
  },
  "entrypoints": {
    "vectorTileUrl": "https://tiles.maps.etzhayyim.com/v1/{z}/{x}/{y}.pbf",
    "demTileUrl": "https://elevation.example/{z}/{x}/{y}.png",
    "styleUrl": "https://tiles.maps.etzhayyim.com/v1/style.json"
  }
}
```

### Graph Write Contract

graph 側には実アセット本体ではなく、次の参照情報を書く。

- `Asset`
  - `asset_type = "kami_street_chunk"`
  - `format = "glb+ktx2+json"`
  - `chunk_key`
  - `lod_count`
  - `compressed_bytes`
  - `source_did`
- `SpatialVersion`
  - `version`
  - `bbox`
  - `build_job_id`
  - `quality_class`
  - `published_at`

### KAMI Consumption Rules

- descriptor の `budget` を超える chunk は publish しない
- `vectorSources` / `terrainSources` は renderer fallback 選択にのみ使う
- geometry の canonical runtime format は `GLB`
- `3DGS` / `NeRF` は descriptor には出さない

## Operational Rule

`maps.etzhayyim.com` は raw imagery platform ではなく、**street imagery を graph-backed game asset へ変換する control plane** と位置付ける。`kami engine` はその結果を実行する renderer / simulation runtime とする。

## Cosmic Runtime Extension

2026-04-17 時点で `maps.etzhayyim.com` の KAMI runtime は street / globe だけでなく、`Earth -> Cislunar -> Solar System -> Milky Way -> Observable Universe` まで連続 zoom-out できる cosmic scene を持つ。

### Runtime Policy

- Earth / terrain / vector overlay は `kami-map` の同一 renderer が担当する
- cosmic scene は app 側の fake overlay ではなく `kami-map` の engine-native mesh と camera で描く
- `ISS` と TLE を持つ衛星は `sgp4` propagation を使う
- `Moon / GEO belt / planets / galactic spiral / universe shell` は graph-backed orbital/celestial config から scene assembly する

### Graph Integration

Cosmic scene の source of truth は graph に置く。

- `vertex_orbital_system`
- `vertex_orbital_body`
- `vertex_celestial_catalog`
- `vertex_celestial_object`

責務分離は次の通り。

- `orbital_system`: frame hierarchy
- `orbital_body`: Earth/Moon/ISS/GEO/TDRS/GOES などの orbiting body と TLE
- `celestial_catalog`: authority / frame / coverage の catalog
- `celestial_object`: Solar System / Milky Way / Andromeda / Observable Universe の hierarchy

### Current Seed Scope

graph には少なくとも以下を seed している。

- orbital: Earth, Moon, Sun, ISS, GEO belt
- live TLE satellites: TDRS 3, TDRS 12, GOES 16, GOES 18, HIMAWARI-9, ELEKTRO-L 3, SES-17
- celestial: Solar System, Milky Way, Sagittarius A*, Andromeda, Local Group, Observable Universe

### Ephemeris Policy

- `ISS` および `tle_line1/2` を持つ衛星は `sgp4` crate による propagation
- TLE parse は毎フレームではなく `kami-map` の cache に保持し、line 変更時のみ再構築
- 巨大スケール差は runtime scene で圧縮表示する
  - cislunar: power-scale compression
  - solar: cube-root scale compression
  - galactic / universe: anchor shell rendering

### Worker Contract

`com.etzhayyim.apps.maps.runtimeConfig` は terrain/vector に加えて以下も返す。

- `orbitalSystems`
- `orbitalBodies`
- `celestialCatalogs`
- `celestialObjects`

frontend はそれをそのまま `KamiMapBridge.create()` に渡し、WASM 側が cosmic scene を assemble する。

## Final Answer

このリポジトリにおける正解は次の一文に要約できる。

> Mapillary 画像は最終形式として保持せず、`maps.etzhayyim.com` で選別・再構成・意味抽象化し、`kami engine` には LoD 付き mesh + baked textures + compressed glTF を渡す。

NeRF / 3DGS は高品質再構成のためのオーブンであり、食卓に出す形式ではない。
