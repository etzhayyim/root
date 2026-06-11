# Maps Forward Topology: Raw Source → WebGPU 3D (No PNG Pyramid)

**Status**: design
**Date**: 2026-04-17
**Context**: maps.etzhayyim.com は現在 OSM raster PNG tiles (`tile.openstreetmap.org/{z}/{x}/{y}.png`) を KAMI `upload_tile` で basemap として使用。ベクタ (`tileGeoJson`) と 3D 建物 (`addExtrudeLayer`) は Kotoba/Datomic-native だが、**basemap 自体は XYZ pyramid pre-rendered raster** に依存している。
**Goal**: OSM / Mapraly / Mapillary / Satellite の **raw 一次データ** から、**XYZ pyramid を介さず**、realtime に WebGPU で 3D レンダリングする forward topology を確立する。

## 用語

- **逆トポロジー (inverse topology)**: XYZ tile pyramid (Web Mercator Z/X/Y)。上位ノード (low-z) は下位 (high-z) の集約で生成され、データが client に届くとき pyramid の leaf から root に向かって参照される「逆向き」の木構造。pre-rendering 前提。
- **順トポロジー (forward topology, 本文書の設計)**: 一次ソース (OSM PBF / Mapillary JPEG / Sentinel-2 COG / Kotoba/Datomic vertex) から、projection layer (streaming MV) を経て、`Chunk` という空間単位で client が直接参照する DAG。pre-rendering なし。

## 現状 (参考)

```
XYZ PNG pyramid (逆トポロジー)
  tile.openstreetmap.org/{z}/{x}/{y}.png  ── raster 一方向依存 ──▶  KAMI upload_tile
                                                                       │
com.etzhayyim.apps.maps.tileGeoJson  ── GeoJSON  ─────────────────────────▶  KAMI addLayer (line/fill/circle)
                                                                       │
                                                  (building polygons) ─▶  KAMI addExtrudeLayer  (3D)
                                                                       │
elevation-tiles-prod.s3 terrarium/{z}/{x}/{y}.png  ── DEM raster ─────▶  KAMI upload_dem_tile
```

問題:
1. **OSM planet PNG pyramid** (OSM.org のタイル) はデータ更新から数日〜数週間遅延。raw OSM edit は反映されない。
2. **Mapillary 街路画像** は現状未使用 (raster なし、3D mesh もなし)。
3. **衛星 COG** (Sentinel-2 / Landsat) も raw を直接 WebGPU に流していない。
4. **DEM terrarium** は outside 3rd party (elevation-tiles-prod.s3.amazonaws.com)、制御外。
5. **Pre-rendering コスト** が planet-scale で非現実的。Kotoba/Datomic にあるのに PNG に焼き直すのはエントロピー冗長。

## Forward Topology Design

### Layer 0 — Source (already exists, 確認のみ)

| Source | Worker | Graph tables |
|---|---|---|
| OSM Planet PBF | `70-tools/maps-osm-ingest` (Rust) + `50-infra/k8s/maps-tilemaker-build` (K8s CronJob) | `vertex_osm_element` + `edge_osm_way_node` + `edge_osm_relation_member` + `mv_osm_tag_lookup` (migration 0055) |
| Mapraly POI/route | `mapraly_ingest` XRPC | `vertex_spatial` (Spot/Route) |
| Mapillary street imagery | (未配線) | 計画: `vertex_mapillary_image` + `vertex_mapillary_sequence` |
| Sentinel-2 / Landsat COG | `satellite_ingest` (STAC) | `vertex_satellite_scene` |
| User post EXIF | `extract_post_location` | `vertex_spatial` (Place) |

### Layer 1 — Projection (Kotoba/Datomic streaming MV, 逆トポロジー外)

**OSM way + node を polygon / line に集約する MV を追加する。XYZ pyramid は一切作らない。**

```sql
-- Building polygons from OSM way + tags (streaming MV, < 100ms freshness)
CREATE MATERIALIZED VIEW mv_osm_building_polygon AS
SELECT
  w.osm_id,
  ST_MakePolygon(ST_MakeLine(array_agg(n.geom ORDER BY wn.seq))) AS geom,
  (t.tags ->> 'height')::DOUBLE PRECISION           AS height_m,
  (t.tags ->> 'building:levels')::INT                AS levels,
  t.tags ->> 'building'                              AS building_type,
  t.tags ->> 'name'                                  AS name,
  h3_lat_lng_to_cell(ST_Y(ST_Centroid(...)), ST_X(...), 8) AS h3_res8_cell,
  h3_lat_lng_to_cell(..., 6) AS h3_res6_cell,
  h3_lat_lng_to_cell(..., 4) AS h3_res4_cell
FROM vertex_osm_element w
JOIN edge_osm_way_node wn ON wn.way_id = w.osm_id
JOIN vertex_osm_element n ON n.osm_id = wn.node_id
JOIN mv_osm_tag_lookup t ON t.osm_id = w.osm_id
WHERE t.tags ? 'building'
GROUP BY w.osm_id, t.tags;

-- 同じパターンで road/river/railway/coastline/admin_boundary
```

**H3 cell column を全 polygon/line row に付与** する。これが `Chunk` key になる。XYZ pyramid の代替。

### Layer 2 — Chunk (空間単位、逆トポロジー外の flat key)

**Chunk = H3 cell × LOD (resolution)** で空間を分割する。XYZ pyramid と違い:
- **どの LOD も対等** (parent-child 関係を持たない平坦な key)
- H3 は球面均等分割 (Web Mercator の極緯度歪みなし、3D rendering 向き)
- Client は現在の zoom から適切な resolution を選び、viewport を cover する cell を直接クエリ

| LOD | H3 resolution | 平均 cell 辺長 | 想定 zoom 範囲 | 1 cell あたりの features (目安) |
|---|---|---|---|---|
| L0 | res 2 | 1,600 km | 地球〜国 | ~10M (admin_area のみ) |
| L1 | res 4 | 230 km | 国〜広域 | ~1M (coastline, major road) |
| L2 | res 6 | 32 km | 都道府県 | ~100k (road, river, city boundary) |
| L3 | res 8 | 4.6 km | 市町村 | ~10k (building, railway, poi) |
| L4 | res 10 | 680 m | 街区 | ~1k (detailed building, street) |
| L5 | res 12 | 95 m | 建物単位 | ~100 (door-level, indoor) |

Client は `viewport → visibleH3Cells(resolution) → chunk query` する。

### Layer 3 — Chunk XRPC (replaces tileGeoJson)

```
com.etzhayyim.apps.maps.getChunk
  input:  { h3Cells: string[], lod: 0-5, labels: string[], format: "geojson" | "binary" }
  output: { chunks: { [h3Cell]: { [label]: Feature[] } } }

com.etzhayyim.apps.maps.subscribeChunks (wRPC stream)
  input:  { h3Cells: string[], lod: int, labels: string[] }
  stream: { h3Cell: string, label: string, delta: "upsert" | "delete", feature: Feature }
```

**差分**: 旧 `tileGeoJson` が bbox + label で lat/lng フィルタして返すのに対し、`getChunk` は H3 cell をキーにする。`vertex_spatial` の `h3_res{N}_cell` column で O(1) で引ける (B-tree index)。viewport 変化時、client は visible cell の差集合だけ新規リクエスト → 既存 cache を reuse。

**Streaming**: `subscribeChunks` は `sdk.app.handleStream` 経由の wRPC。OSM / Mapillary の新 commit が入ると projection MV が更新 → stream に delta が push → client が追加レンダー。realtime 保証。

### Layer 4 — Binary format (optional, for large chunks)

GeoJSON は human-readable だが density 低 (text + JSON overhead)。L4/L5 の巨大 chunk (建物数千) では FlatGeobuf か MVT (decode in KAMI WASM、既存 `decode_mvt_layer` を流用) を検討。

**Phase 1**: GeoJSON のみ。L4 でも ~500 KB/chunk gzip で収まる想定。
**Phase 2**: FlatGeobuf に switch (reader は kami-map に追加、~2 KLOC Rust)。

### Layer 5 — Client rendering (KAMI WebGPU)

```
visibleH3Cells(viewport, lod)
  │
  ├─ already in cache? ──▶  reuse
  │
  └─ miss ──▶  getChunk XRPC ──▶  cache ──▶  per label:
                                                │
                                                ├─ Polygon → addFillLayer or addExtrudeLayer (if heightM)
                                                ├─ LineString → addLineLayer
                                                └─ Point → addCircleLayer
```

すでに KAMI には `add_fill_layer` / `add_line_layer` / `add_circle_layer` / `add_extrude_layer` が揃っているので**新規 shader は不要**。必要なのは:
1. **Client-side H3 visibility calculator** (TypeScript、`h3-js` library、~50 LOC)
2. **Chunk cache** (Map<h3Cell, LoadedChunk>、LRU 1024 エントリ、~100 LOC)
3. **Streaming subscriber** (wRPC `subscribeChunks` に bbox 変化のたび subscribe/unsubscribe、~150 LOC)

### Raster 代替 (basemap without PNG)

OSM raster PNG pyramid を完全に捨てるには、低 zoom の「世界が見える」表現が必要。3 オプション:

| 方式 | 実装 | 長所 | 短所 |
|---|---|---|---|
| **A. Full vector basemap** | L0-L2 の OSM polygon/line を全部 getChunk で配信 | PNG 完全不要、data-live | 低 zoom で features 多すぎ (coastline 世界 ~100MB) |
| **B. Pre-computed vector coastline + landmass** | `mv_world_landmass_simplified` を作り、L0 固定 payload (~5MB) を 1 回だけ fetch | 低 zoom 軽量、PNG 不要 | simplify 処理が事前必要 (streaming MV で可能) |
| **C. Hybrid: Satellite COG for low zoom, vector for high** | Sentinel-2 COG を L0-L1 で WebGPU texture に直接流し、L2+ で vector | 地形感がある、壁紙として自然 | COG decoder が WASM 側に必要 |

**推奨: B + C の組み合わせ**。L0 landmass は 1 回 fetch、L1 以降は H3 chunk、低 zoom 地球ビューは optional で COG。OSM.org への依存をゼロにする。

### Update cadence

- OSM PBF 全差分 → `maps-osm-ingest` の K8s CronJob が 1 時間ごとに diff apply → streaming MV 自動更新 → subscribeChunks 経由で client に push
- Mapraly POI → webhook or 1 日 1 回 polling → 同上
- Mapillary → webhook on new upload → 同上
- Satellite → STAC new scene → 差分のみ

**一次ソース → client 到達時間**: target **< 60 秒** (OSM diff 1 h cadence は現状制約、将来 Overpass Streaming API 検討)

## 比較: 逆トポロジー vs 順トポロジー

| 観点 | XYZ PNG pyramid (逆) | H3 Chunk graph (順) |
|---|---|---|
| Pre-render cost | planet-scale render (~$$$/月) | 0 (streaming MV で projection のみ) |
| Freshness | 日〜週 | < 60 秒 |
| 3D native | no (raster は常に 2D) | yes (polygon + height_m が geometry) |
| Mapillary/Satellite 取り込み | 別 pipeline 必要 | graph に直接 ingest、同じ Chunk |
| Viewport query | Z/X/Y 計算 | H3 visibility 計算 (GPU frustum cull でさらに subset) |
| 球面歪み | Mercator 極緯度 2x 誤差 | H3 は均等 |
| Client cache | tile key (単純) | h3Cell key (同じく単純) |
| Delta update | 不可 (tile 全体差し替え) | feature-level delta (wRPC stream) |
| Parent/child LOD | pyramid 強制 | 独立 (LOD 選択は client 任意) |
| Shannon η | 低 (pre-render 冗長) | 高 (一次ソース → 描画まで 0 redundancy) |

## 実装順序 (follow-up migrations)

1. **[[migrations]] maps-h3-chunk-projection**: `vertex_spatial` + OSM MV に `h3_res{4,6,8,10}_cell` column を migration 追加、back-fill
2. **[[migrations]] maps-forward-topology-xrpc**: `com.etzhayyim.apps.maps.getChunk` + `subscribeChunks` lexicon + handler
3. **[[migrations]] maps-client-chunk-renderer**: Svelte 側に `visibleH3Cells` + chunk cache + stream subscriber。既存 `kotoba-overlay.ts` をリプレース
4. **[[migrations]] maps-osm-basemap-coastline**: `mv_world_landmass_simplified` 生成 + L0 endpoint、OSM.org PNG 依存除去
5. **[[migrations]] maps-satellite-cog-webgpu** (optional): COG decoder を kami-map に追加、低 zoom basemap に整合
6. **[[migrations]] maps-mapillary-chunks** (optional): Mapillary imagery を H3 chunk に紐づけ、`asset:image` DID で CAS 参照

各 phase 独立に deploy 可能。Phase 1+2+3 で OSM.org PNG への現在の依存は切れる。

## Shannon 根拠

- **Pre-render 除去**: planet-scale PNG pyramid は output 冗長度が高い (同じ OSM record が複数 zoom tile に複製される)。Streaming MV は projection を一度だけ持ち、LOD は H3 resolution で選ぶ (冗長 0%)
- **Transport 単一**: XYZ (HTTP GET image) + XRPC (POST JSON) の二重 transport が `getChunk + subscribeChunks` 一種 (XRPC + wRPC stream) に統合
- **Update channel 単一**: PNG は polling / cache-bust、vector は同じ wRPC stream で delta push。二経路 → 一経路
- η 推定: 現状 ~0.45 (PNG pyramid + tileGeoJson の併存、pre-render コスト、freshness gap) → forward topology で ~0.90

## 決めること (ユーザ確認)

1. **Phase 1 (h3-chunk-projection) から着手で良いか?** DB migration + back-fill は数時間の graph Worker 停止を伴う可能性
2. **L0 basemap**: Option B (landmass vector, pre-computed) か Option C (satellite COG) か両方か
3. **Binary format timing**: GeoJSON で Phase 1-3 を済ませ、Phase 4+ で FlatGeobuf 検討で可か
4. **OSM PNG fallback**: 移行期間中は PNG を keep するか、即切るか

承認があれば `[[migrations]] maps-h3-chunk-projection` から着手する。
