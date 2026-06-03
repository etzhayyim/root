# crawler → land-owners 正規化 → maps.etzhayyim.com 表示 設計

## 1. 目的と前提
- 目的: `crawler` で土地所有者情報ソースを収集し、`land-owners` で正規化・永続化し、`maps.etzhayyim.com` で地図表示する。
- 前提（現状実装）:
  - `crawler-mcp-component` は MCP (`https://crawler.etzhayyim.com/api/mcp`) と REST を提供し、crawl job / result を KV + Quickwit に保存。
  - `land-owners-crawler-component` は `POST /api/crawler/collect` と `GET /api/map/geojson` を提供するが、現在は in-memory 保存。
  - `maps-ui-uqpel6i6` は `MAP_CRAWLER_MCP_URL` で crawler を参照し、`/api/map/search/resources` を提供。

## 2. 現状ギャップ
- `land-owners` は永続化されず、再起動で消失する。
- `crawler` のページ結果 (`crawler.list_results`) から土地所有者エンティティへの抽出経路が未定義。
- `maps.etzhayyim.com` には land-owners 専用レイヤー API が未接続。
- フロント新規APIは XRPC 方針だが、land-owners 表示系の契約が未整備。

## 3. 目標アーキテクチャ
1. `crawler` が登記・自治体公開データ・公告ページを crawl。
2. `land-owners` の正規化ワーカーが crawler 結果を取り込み、所有者レコードへ正規化。
3. 正規化済みレコードを `performer/rdbms` (cypher graph RDBMS) に保存（必要に応じて Quickwit 二次インデックス）。
4. `maps.etzhayyim.com` は land-owners GeoJSON API/Connect API から取得しレイヤー表示。

```text
crawler-mcp-component
  -> (MCP tools: crawler.list_jobs / crawler.list_results)
land-owners-normalizer (new)
  -> (dedupe/normalize/geocode)
land-owners-api (existing component expanded)
  -> /api/map/geojson?country=&region=&owner_type=
maps.etzhayyim.com
  -> layer render + search
```

## 4. データモデル（正規化後）
`LandOwnerRecordNormalized`
- `record_id`: string (`sha256(country|parcel_id|owner_name_norm|source_doc_id)` 推奨)
- `parcel_id`: string
- `parcel_id_norm`: string（国別正規化ルール適用）
- `owner_name`: string
- `owner_name_norm`: string（全角半角・法人表記ゆれ吸収）
- `owner_type`: enum (`public|private|ngo|cooperative|unknown`)
- `country`: ISO-3166-1 alpha2
- `region`: string
- `address_raw`: string
- `latitude` / `longitude`: float64
- `confidence`: float (0-1)
- `evidence_url`: string
- `source`: string (`crawler` / `registry-api` / `manual`)
- `source_doc_id`: string (`crawler result_id`)
- `collected_at` / `normalized_at`: RFC3339

GeoJSON properties:
- `record_id`, `parcel_id`, `owner_name`, `owner_type`, `country`, `region`, `confidence`, `evidence_url`, `source`, `normalized_at`

## 5. 処理フロー設計
### 5.1 収集（crawler）
- 実行: `crawler.start_crawl`（seed profile + 対象ドメイン）
- 取得: `crawler.list_results` で `title/url/text_content/crawled_at` を取得。
- ソース分類タグ（推奨追加）: `land_registry`, `municipality_notice`, `auction`, `tax`。

### 5.2 抽出・正規化（land-owners normalizer）
- 入力: crawler results。
- 抽出:
  - 規則ベース（parcel表記、地番、所有者名パターン）
  - 必要に応じてLLM補助（低confidence時のみ）
- 正規化:
  - `country` upper-case
  - `owner_name` の suffix/prefix 正規化（株式会社/Inc./Ltd. の統一辞書）
  - `parcel_id` のフォーマット標準化
  - 座標がない場合は geocode（結果に `confidence` 反映）
- 重複排除:
  - 主キー `record_id` upsert
  - 近接座標 + 同一 owner_name_norm + parcel_id_norm で同一判定

### 5.3 保存
- KV bucket 例: `land-owners-state`
- Key設計:
  - `landowner:record:<record_id>`
  - `landowner:index:country:<CC>:<record_id>`
  - `landowner:index:region:<CC>:<region_norm>:<record_id>`
  - `landowner:index:parcel:<country>:<parcel_id_norm>`
- in-memory はキャッシュのみ。SoT は KV。

### 5.4 配信
- 既存 REST を維持しつつ拡張:
  - `GET /api/land-owners/records?country=&region=&owner_type=&limit=&cursor=`
  - `GET /api/map/geojson?country=&region=&owner_type=&bbox=&zoom=`
- 新規推奨（フロント向け）:
  - XRPC `com.etzhayyim.apps.jinushi.listMapFeatures`

## 6. maps.etzhayyim.com 統合
- maps backend (`maps-ui-uqpel6i6/main.go`) に `searchWithLandOwners` を追加。
- 検索統合優先順位:
  1. land-owners（地物）
  2. crawler/quickwit（文書）
  3. resources（法令/参照）
- UI:
  - land-owners レイヤートグル
  - owner_type 別色分け
  - タップ時に evidence URL と confidence を表示

## 7. デプロイ・ルーティング方針（必須制約反映）
- `default` namespace への作成は禁止。
- 配置:
  - App platform/system: `magatama-system`
  - WADM app resources: `magatama-runtime`
  - HTTPRoute: `etzhayyim-performers-org-etzhayyim`
- 既存運用と合わせ、`mage Deploy` でデプロイ。
- 画像配布は `ghcr.io/etzhayyim/*` のみ。

## 8. 可観測性・品質ゲート
- 指標:
  - `landowners_ingested_total`
  - `landowners_normalize_fail_total`
  - `landowners_dedupe_merged_total`
  - `landowners_geojson_served_total`
- 品質KPI:
  - 正規化成功率 >= 95%
  - geocode 付き率 >= 85%
  - duplicate率（統合前後）
  - maps表示遅延 p95 < 500ms

## 9. 実装フェーズ
1. Phase 1 (MVP)
- `land-owners` を KV 永続化化（in-memory廃止）
- crawler results -> landowner ingest バッチを追加
- `GET /api/map/geojson` に `owner_type/bbox/limit` を追加

2. Phase 2
- XRPC API 追加
- maps の land-owners レイヤーと検索統合
- dedupe/geocode 改善

3. Phase 3
- Quickwit インデックス最適化
- 変更差分配信（更新通知）
- 低confidence案件の review queue 化

## 10. 主要インターフェース（最小）
- crawler MCP:
  - `crawler.list_jobs`
  - `crawler.list_results`
- land-owners MCP（既存拡張）:
  - `crawler_ingest_record`
  - `landowners_query_region`
  - 推奨追加: `landowners_ingest_from_crawler_result`, `landowners_list_map_features`

---
この設計で、既存資産（crawler MCP / maps API）を活かしつつ、land-owners を「正規化SoT」として maps 表示へ安定接続できる。
