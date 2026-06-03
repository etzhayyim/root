---
id: maps-vision-satellite-pipeline
title: Maps Vision & Satellite Pipeline Design
status: active
doc_type: reference
topic: maps-vision-satellite
authoritative: true
last_verified: 2026-03-28
authoritative_for:
  - maps image analysis pipeline
  - maps satellite data integration
  - maps EXIF geolocation extraction
  - maps Mapraly ingest
related:
  - maps-claude
  - pds-yata-r2-lexicon-process-map
supersedes: []
superseded_by: []
---

# Maps Vision & Satellite Pipeline Design

maps.etzhayyim.com の画像分析・衛星データ統合パイプライン設計。4 段階で User Post EXIF → Mapraly → Murakumo Vision → Satellite を統合。

## Goal

- ユーザー投稿、Mapraly、画像分析、衛星写真の 4 ソースから空間エンティティを抽出し、DID・ノードに紐付ける
- 全ソースを path-based DID で provenance 管理
- 既存の Collection Job Pattern + Design E 3-Tier Write に準拠

## Scope

maps-ui (`uqpel6i6`) の 14 新コマンド + handleCommit 拡張。maps-collection は既存のまま。

## Executive Summary

| Step | Source | Source DID | コマンド数 | 出力ノード |
|---|---|---|---|---|
| 1 | User Post EXIF | `did:web:maps.etzhayyim.com:user_post` | 2 | SpatialEvent, Place |
| 2 | Mapraly | `did:web:maps.etzhayyim.com:mapraly` | 3 | Spot, Route, CollectionJob |
| 3 | Murakumo Vision | `did:web:maps.etzhayyim.com:vision` | 3 | VisionResult + 任意エンティティ |
| 4 | Satellite (STAC) | `did:web:maps.etzhayyim.com:satellite` | 5 | SatelliteScene, CollectionJob |

## Decision

### Source DID 追加

| DID | 外部ソース | TTL |
|---|---|---|
| `did:web:maps.etzhayyim.com:user_post` | app.bsky.feed.post 画像 EXIF | 無期限 |
| `did:web:maps.etzhayyim.com:mapraly` | Mapraly REST API | 7d |
| `did:web:maps.etzhayyim.com:vision` | Murakumo Vision (qwen3-vl-8b) | 無期限 |
| `did:web:maps.etzhayyim.com:satellite` | Sentinel-2/1, Landsat, HLS, Copernicus DEM, NAIP (全無料 STAC) | 30d |

### Graph Schema 追加

**Node Labels (+3 = 47 total)**:
- `VisionResult` — 画像分析結果 (confidence, detected_classes, entity reference)
- `SatelliteScene` — 衛星シーンメタデータ (bbox, bands, COG URL, cloud cover)
- `CollectionJob` — 収集ジョブ (全ソース共通、status: pending→running→completed/failed)

**Edge Types (+3)**:
- `DETECTED` — VisionResult → 検出エンティティ
- `SAME_AS` — ソース間の同一エンティティ紐付け (距離 < 50m)
- `ANALYZED_FROM` — 分析結果 → ソース画像/シーン

## Pipeline Architecture

### Step 1: User Post EXIF → SpatialEvent (最低コスト、Murakumo 不要)

```
app.bsky.feed.post (image embed + EXIF lat/lng)
  → handleComAtprotoSyncSubscribeReposCommit (reactive)
    → embed JSON parse → EXIF {lat, lng, altitude, timestamp, camera} 抽出
    → SpatialEvent (event_type: "user_post_photo") 自動生成
    → 近傍 50m 以内に Place なければ Place 自動生成
    → social post: [GeoPhoto] Auto-located at {lat},{lng}
```

**コマンド**:
| Command | Description |
|---|---|
| `extract_post_location` | 手動 EXIF 抽出 (post_uri + embed_images + exif) |
| `list_post_locations` | author/area で geolocated posts 一覧 |

### Step 2: Mapraly Ingest (Collection Job Pattern)

```
mapraly_ingest (region/bbox)
  → CollectionJob record (source: "mapraly", status: "pending")
  → [async: PDS pipeline fetches Mapraly API]
  → mapraly_import_poi (batch POI/route import)
    → route_geojson あり → Route node
    → route_geojson なし → Spot node (spot_type: "mapraly_poi")
  → social post: [Mapraly] Imported N POIs/routes
```

**コマンド**:
| Command | Description |
|---|---|
| `mapraly_ingest` | Mapraly collection job 作成 (region or bbox) |
| `mapraly_import_poi` | POI/route batch import (Mapraly → Spot/Route) |
| `mapraly_list_pois` | Mapraly ソースの POI 一覧 (category/area filter) |

### Step 3: Murakumo Vision → Entity Extraction

```
analyze_image (image_cid/image_url + lat/lng + analysis_type)
  → CollectionJob record (source: "murakumo_vision", status: "pending")
  → [async: Murakumo LLM qwen3-vl-8b multimodal analysis]
    → prompt: "Extract spatial entities: buildings, roads, vegetation, water, POIs"
  → vision_import_entities (batch entity import)
    → entity.kind → 対応する LABEL_MAP ノード (Building, Spot, Place, etc.)
    → VisionResult ノード (confidence, classes, entity reference)
  → social post: [Vision] Extracted N spatial entities
```

**分析タイプ**:
| analysis_type | 入力 | 出力 |
|---|---|---|
| `spatial_entity_extraction` | 任意画像 | Building, Spot, Place, Road |
| `land_use_classification` | 航空写真/衛星 | AdminArea, Spot (land_use) |
| `building_detection` | 衛星/ストリートビュー | Building (footprint, height) |
| `infrastructure_detection` | ストリートビュー | InfraNode, InfraSegment |
| `change_detection` | 衛星時系列 | SpatialEvent (変化箇所) |

**コマンド**:
| Command | Description |
|---|---|
| `analyze_image` | 画像分析ジョブ作成 (Murakumo Vision) |
| `vision_import_entities` | 分析結果エンティティ batch import |
| `list_vision_results` | 分析結果一覧 (job/kind/confidence filter) |

### Step 4: Satellite Imagery (STAC + Vision)

```
satellite_ingest (bbox + date_from/to + satellite + max_cloud_cover)
  → CollectionJob record (source: "satellite", format: "stac_cog")
  → [async: STAC catalog query → scene metadata]
  → satellite_import_scene (batch scene import)
    → SatelliteScene node (scene_id, bbox, bands, cog_url, cloud_cover)
  → satellite_analyze (scene_id → Vision 分析 collection_job)
    → [async: Murakumo Vision on COG/thumbnail]
    → vision_import_entities → 抽出エンティティ
```

**コマンド**:
| Command | Description |
|---|---|
| `satellite_ingest` | 無料 STAC catalog collection job (sentinel-2/landsat/sentinel-1/hls/cop-dem/naip) |
| `satellite_import_scene` | scene metadata batch import (sensor_type, stac_collection_id) |
| `satellite_analyze` | scene → Murakumo Vision 分析ジョブ |
| `list_satellite_scenes` | scene 一覧 (satellite/area/date filter) |
| `list_satellite_sources` | 利用可能な無料衛星データソース一覧 |

## Satellite Data Sources

### Tier 0: 無料 (FREE_SATELLITE_CATALOG — 実装済み)

`list_satellite_sources` コマンドで一覧取得可能。

| Name | STAC Endpoint | Collection ID | 解像度 | 再訪 | センサー | 用途 |
|---|---|---|---|---|---|---|
| `sentinel-2` | `earth-search.aws.element84.com/v1` | `sentinel-2-l2a` | 10m | 5日 | optical (13 VNIR/SWIR) | 土地利用、NDVI、変化検出 |
| `landsat` | `landsatlook.usgs.gov/stac-server` | `landsat-c2l2-sr` | 30m | 8日 | optical (11 OLI/TIRS) | 50年アーカイブ、温度、長期変化 |
| `sentinel-1` | `earth-search.aws.element84.com/v1` | `sentinel-1-grd` | 10m | 6日 | SAR (C-band VV+VH) | 洪水、地盤沈下、全天候 |
| `hls` | `cmr.earthdata.nasa.gov/stac` | `HLSL30.v2.0` | 30m | 3日 | optical (6 harmonized) | 高頻度時系列 |
| `cop-dem` | `earth-search.aws.element84.com/v1` | `cop-dem-glo-30` | 30m | — | DEM | 標高、地形解析 |
| `naip` | `planetarycomputer.microsoft.com/api/stac/v1` | `naip` | 1m | 2年 | aerial (RGBNIR) | 米国のみ、建物検出 |

その他の無料ソース (STAC 未統合):
- **JAXA G-Portal**: ALOS-2 L-band SAR (1m) + ALOS World 3D (30m DEM) — 研究無料
- **Planet Education**: PlanetScope 3m 日次 2016年〜 — 学術・非営利限定、申請制
- **Umbra Open Data**: 0.16-1m SAR サンプル — AWS Registry
- **Maxar Open Data**: 0.3m — 災害時公開分のみ
- **Planet NICFI**: 4.77m 月次 — 熱帯森林、非商用

### 無料ソースの組み合わせで実現できること

| ユースケース | ソース組合せ | 精度 |
|---|---|---|
| 変化検出 (建物新築、道路) | Sentinel-2 (5日) + HLS (3日) | 10-30m で変化箇所特定 → Murakumo Vision で詳細分析 |
| 洪水マッピング | Sentinel-1 SAR (全天候) | 10m、雲の影響なし |
| 地盤沈下 (InSAR) | Sentinel-1 SAR 時系列 | mm 精度の沈下検出 |
| 土地利用分類 | Sentinel-2 (13 band) | 10m、NDVI/NDWI/NDBI |
| 標高・地形 | Copernicus DEM | 30m 全球 |
| 米国建物検出 | NAIP (1m aerial) | 建物フットプリント抽出可能 |
| 長期変化 (50年) | Landsat アーカイブ | 30m、1972年〜 |

### 商用アーカイブ (タスキング不要) — コスト比較

**タスキング (新規撮影注文) は不要。** 既存アーカイブ (過去の撮影済み画像) のみ。タスキングはアーカイブの 5-10 倍高い。

#### 東京 10,000 km² 正規化比較

| 順位 | プロバイダ | 解像度 | アーカイブ費用 | アーカイブ開始 | 購入方法 |
|---|---|---|---|---|---|
| 1 | **Jilin-1** (中国国内) | 0.75m | **$3K-7K** | 2015年 | jl1mall.com (中国チャネル) |
| 2 | **Satellogic** | 0.7m | **$15K-30K** (volume: $5-10K) | 2020年 | Aleph platform, API, STAC |
| 3 | **Jilin-1** (国際) | 0.5m | **$20K-50K** | 2015年 | HEAD Aerospace |
| 4 | **Airbus SPOT** | 1.5m | **$20K-50K** | **1986年** | OneAtlas |
| 5 | **Planet PlanetScope** | 3m 日次 | **$20K/年〜** サブスク | 2016年 | planet.com API |
| 6 | **SI Imaging (KOMPSAT)** | 0.4m | **$40K-100K** | 2006年 | si-imaging.com |
| 7 | **Maxar SecureWatch** | 0.3m | **$50K-150K/年** サブスク | **2001年** | SecureWatch (streaming) |
| 8 | **BlackSky** | 1m | **$50K-150K** | 2019年 | Spectra platform |
| 9 | **Airbus Pleiades** | 0.5m | **$100K-170K** | 2012年 | OneAtlas |
| 10 | **Maxar** 単発 | 0.3m | **$100K-250K** | 2001年 | per-scene |
| 11 | **Capella SAR** | 0.5m | **$140K-200K** | 2020年 | Console, STAC |

#### 全球サブスク比較 (アーカイブ閲覧)

| プロバイダ | 年額 | 解像度 | 内容 | 制限 |
|---|---|---|---|---|
| **Airbus OneAtlas Discover** | **€3,600** (~$4K) | 0.3-1.5m | Pleiades Neo + Pleiades + SPOT | 月 50K tiles (~3K km²)。ストリーミングのみ |
| **Airbus OneAtlas Standard** | **€10K-15K** | 0.3-1.5m | 同上 | 月 500K tiles (~30K km²)。★ 全球コスパ最良 |
| **Airbus OneAtlas Premium** | **€30K-60K** | 0.3-1.5m | 同上 + SAR | 月 1.5M tiles (~90K km²) |
| **Planet Basic Monitor** | **$5K-10K** | 3m 日次 | PlanetScope AOI 内 | AOI サイズ制限 |
| **Planet Plus** | **$20K-50K** | 3m 日次 + SkySat | PlanetScope + SkySat AOI 内 | 日次変化検出に最適 |
| **Maxar SecureWatch** | **$10K-250K** | 0.3m | WV archive (2001年〜) | AOI + ストリーミングのみ。DL 別途 |

**注意**: 全サブスクにタイル/AOI 上限あり。真の「取り放題」は存在しない。

#### マーケットプレイス/リセラー (アーカイブ、タスキング不要)

| サービス | 扱いデータ | アーカイブ価格 | 最低注文 | API |
|---|---|---|---|---|
| **SkyWatch** (EarthCache) | 30+ プロバイダ横断 | $3-8/km² | 5 km² | REST API, STAC |
| **UP42** (Airbus 子会社) | Airbus, Planet, 21AT | €100〜 (クレジット制) | 0.01 km² | REST API, STAC |
| **Geocento** (EarthImages) | 30+ プロバイダ横断 | $10-20/km² VHR | 25 km² | Catalog API |
| **HEAD Aerospace** | 中国衛星 (SuperView/Jilin-1) | **$3-5/km²** | 25 km² | Manual |
| **APOLLO Mapping** | Maxar, Airbus, Planet | $14-20/km² VHR | 25 km² | Manual |

#### 衛星ビデオ アーカイブ

| プロバイダ | アーカイブ価格 | 解像度 | 1clip 長さ | アーカイブ量 |
|---|---|---|---|---|
| **Jilin-1** | **$200-500/clip** | 75cm-1m 25fps | 60-120秒 | 数万本 (2015年〜) |
| **SkySat** (Planet) | **$500-1,000/clip** | ~1m 30fps | 60-90秒 | 数千本 (2013年〜) |
| **BlackSky** | **$300-800/clip** | ~1m | 短時間 | 数千本 (2019年〜) |

1 clip = 1回の撮影パス (衛星が上空通過中の 60-120秒動画)。タスキング (新規撮影) はアーカイブの 5-10倍高い。

#### 3D/ステレオ

| プロダクト | 価格 | 垂直精度 | カバー |
|---|---|---|---|
| **Copernicus DEM 30m** | **無料** (実装済み) | ~4m | 全球 |
| **ALOS World 3D 30m** | **無料** (JAXA G-Portal) | ~5m | 全球 |
| **SRTM 30m** | **無料** (NASA) | ~9m | ±60° |
| **Airbus WorldDEM 12m** | €0.5-5/km² | ~2m | 全球 |
| **Maxar Precision3D 50cm** | $5-20/km² | ~1-2m | 都市中心 |

#### 商用最高解像度 (2026年)

| 種別 | プロバイダ | 解像度 | 備考 |
|---|---|---|---|
| 航空斜め写真 | EagleView/Nearmap | **3-7.5cm** | N/S/E/W 45° 4方向。建物壁面可視。$10K-500K/年 |
| 成層圏バルーン | Near Space Labs | **10cm** | 米国都市限定 |
| 光学衛星 (計画) | Albedo (VLEO) | **10cm** | 2026-27打上予定 |
| SAR衛星 | Umbra | **16cm** | 世界最高SAR。$975/scene〜 |
| SAR衛星 | Capella/ICEYE | **25cm** | 全天候・夜間 |
| 光学衛星 | Maxar WV-3/Legion | **30cm** | 商用光学最高。2001年〜アーカイブ |
| 光学衛星 | Pleiades Neo | **30cm** | 2021年〜 |
| 偵察衛星 (機密) | KH-11 (米軍) | **~5-10cm** | 非商用 |

衛星は解像度に関わらず「真上からの鳥瞰」のみ。建物壁面 (ファサード) の撮影は物理的に不可能 (高度 300-600km では 50m ビルが視野角 0.005°)。壁面が必要な場合は航空写真 (EagleView/Nearmap) または Mapillary ストリートビュー (`did:web:maps.etzhayyim.com:street_view` 実装済み)。

### 推奨フェーズ (アーカイブ前提)

```
Phase 1 ($0):      Sentinel-2/1 + Landsat + HLS + Copernicus DEM + NAIP (実装済み)
Phase 2 (~$4K/年):  Airbus OneAtlas Discover → 0.3m ストリーミング閲覧
Phase 3 (~$15K/年): Airbus OneAtlas Standard → 月 30K km² + Planet 3m 日次
Phase 4 (スポット): Satellogic $1-3/km² or SkyWatch $3-8/km² で必要箇所のみ購入
```

## WIT Interfaces (etzhayyim:maps@1.0.0)

4 新 interface 追加 (102 total commands):

```wit
interface post-geolocation {
    extract-post-location: func(params: string) -> result<string, string>;
    list-post-locations: func(params: string) -> result<string, string>;
}

interface mapraly-intelligence {
    mapraly-ingest: func(params: string) -> result<string, string>;
    mapraly-import-poi: func(params: string) -> result<string, string>;
    mapraly-list-pois: func(params: string) -> result<string, string>;
}

interface vision-intelligence {
    analyze-image: func(params: string) -> result<string, string>;
    vision-import-entities: func(params: string) -> result<string, string>;
    list-vision-results: func(params: string) -> result<string, string>;
}

interface satellite-intelligence {
    satellite-ingest: func(params: string) -> result<string, string>;
    satellite-import-scene: func(params: string) -> result<string, string>;
    satellite-analyze: func(params: string) -> result<string, string>;
    list-satellite-scenes: func(params: string) -> result<string, string>;
    list-satellite-sources: func(params: string) -> result<string, string>;
}
```

## Data Flow Summary

```
                    ┌─────────────────────────────────────────────┐
                    │              maps.etzhayyim.com                    │
                    │           (yata Cypher graph)                │
                    │                                              │
  User Post ──EXIF──┤  SpatialEvent ─┐                            │
                    │                │                            │
  Mapraly ──POI────┤  Spot/Route ───┤── SAME_AS ── Place         │
                    │                │           (dedup <50m)      │
  Vision ──LLM────┤  VisionResult ─┤── DETECTED ── Building/Spot │
                    │                │                            │
  Satellite ──STAC──┤  SatelliteScene┤── ANALYZED_FROM            │
                    │                │                            │
                    │  source_did = provenance tracking            │
                    └─────────────────────────────────────────────┘
```

## Exceptions

- EXIF 抽出は handleCommit reactive path のみ (バッチ不要)
- Mapraly API が利用不可の場合、collection_job は failed に遷移
- Murakumo Vision の confidence < 0.5 のエンティティは自動 import しない (手動 import は可)
- 衛星シーンの cloud_cover > max_cloud_cover はフィルタで除外

## References

- maps-ui app.ts: `60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6/src/app.ts`
- WIT: `60-apps/etzhayyim-project-maps/wit/maps/package.wit`
- Collection Job Pattern: `60-apps/CLAUDE.md` §Collection Job Pattern
- Design E 3-Tier Write: `60-apps/CLAUDE.md` §Design E
- Murakumo LLM: `60-apps/etzhayyim-project-murakumo/CLAUDE.md`
- STAC spec: https://stacspec.org/
