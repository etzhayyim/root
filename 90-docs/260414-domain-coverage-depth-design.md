---
id: doc-260414-domain-coverage-depth-design
title: Domain Coverage Depth — kuruma / media_anime / media_gamers 知識グラフ設計
status: active
doc_type: explanation
topic: domain-coverage
authoritative: true
authoritative_for:
  - kuruma-graph-depth
  - media-anime-graph-depth
  - media-gamers-graph-depth
last_verified: 2026-04-14
related:
  - 30-graph/graph-schema/migrations/0025_world_coverage_live_mv.ts
  - 30-graph/graph-schema/migrations/0045_vertex_kuruma_depth.ts
  - 30-graph/graph-schema/migrations/0046_vertex_anime_depth.ts
  - 30-graph/graph-schema/migrations/0047_vertex_game_depth.ts
---

# Domain Coverage Depth — kuruma / media_anime / media_gamers 知識グラフ設計

## Goal

3 つの高価値ドメイン (`kuruma`, `media_anime`, `media_gamers`) をフラットな世界総数 (world_total) から、ドメイン内部の **多層 sub-entity + supply chain + 販売/流通** へ展開。各層に vertex / edge / streaming MV を定義し、`mv_world_coverage_live` を補完する **per-subdomain coverage MV** で深さ方向のカバレッジを可視化する。

## Scope

- Kysely schema (vertex_ / edge_ / mv_) 追加
- `dim_world_domain` にサブドメインを追加し world_total を細分化
- 法人 / 製作者 / キャラクター / マップ / アイテム / 部品 / ストーリ / 取引先 / 販売台数 / 流通台数 / 国別 の 11 角度でカバー
- DID path: AT Protocol repo-PK + hierarchical sub-path (ADR 0019 準拠)

## Decision

### Shared design conventions

- **vertex/edge table 命名**: `vertex_<domain>_<label>`, `edge_<domain>_<reltype>` (例: `vertex_kuruma_model`, `edge_kuruma_contains_part`)
- **promoted columns**: `vertex_id` PK, `_seq`, `created_date`, `sensitivity_ord`, `owner_did` + 各 entity 固有フィールド (P10v2 GraphAr-native pattern を踏襲)
- **DID path**: `did:web:<app>.etzhayyim.com:<layer>:<id>` (例: `did:web:kuruma.etzhayyim.com:model:Q165836`)
- **世界比率**: 各 sub-vertex に `world_total_estimate` を `dim_world_domain` で補足

### A. kuruma — 自動車ドメイン深さ設計

12 vertex + 9 edge + 5 MV。supply chain は Tier 3 まで辿れる。

**Path DID 階層**:
```
did:web:kuruma.etzhayyim.com                             — controller
did:web:kuruma.etzhayyim.com:maker:{qid}                 — OEM (e.g. Toyota, BMW)
did:web:kuruma.etzhayyim.com:model:{qid}                 — 車モデル (Corolla, Camry)
did:web:kuruma.etzhayyim.com:trim:{qid}:{variant}        — グレード (Hybrid, Turbo)
did:web:kuruma.etzhayyim.com:platform:{qid}              — 共有プラットフォーム
did:web:kuruma.etzhayyim.com:part:{oem-or-tier1}:{pn}    — 部品 (engine, ECU, sensor)
did:web:kuruma.etzhayyim.com:supplier:{lei-or-qid}       — サプライヤ (Denso, Bosch) → vertex_legal_entity 参照
did:web:kuruma.etzhayyim.com:plant:{qid}                 — 組立工場
did:web:kuruma.etzhayyim.com:unit:{vin}                  — 個車 (17-char VIN)
did:web:kuruma.etzhayyim.com:dealer:{qid-or-local-id}    — ディーラー → vertex_legal_entity
did:web:kuruma.etzhayyim.com:sales:{model}:{country}:{ym} — 月次販売台数
did:web:kuruma.etzhayyim.com:recall:{campaign-id}        — リコール案件
did:web:kuruma.etzhayyim.com:review:{source}:{id}        — 試乗レビュー
```

**Vertex tables** (12):

| Table | Scope | world_total 推定 |
|---|---|---|
| `vertex_kuruma_model` | 車モデル | 80,000 (existing domain) |
| `vertex_kuruma_trim` | グレード・バリエーション | 500,000 (6.25 × model) |
| `vertex_kuruma_platform` | 車台アーキテクチャ | 3,000 |
| `vertex_kuruma_part` | 部品 (個別) | 10,000,000 |
| `vertex_kuruma_plant` | 組立工場 | 2,000 |
| `vertex_kuruma_unit` | 個車 (VIN) | 1,500,000,000 (vehicle world_total) |
| `vertex_kuruma_sales_monthly` | 月次販売データ (年×国×モデル) | 10,000,000 rows/year |
| `vertex_kuruma_recall` | リコール案件 | 50,000 |
| `vertex_kuruma_review` | レビュー/試乗記 | 5,000,000 |
| `vertex_kuruma_feature` | 装備 (ABS, LKAS, ACC) | 5,000 |
| `vertex_kuruma_generation` | 世代 (第X世代モデル) | 200,000 |
| `vertex_kuruma_safety_rating` | 安全格付け (Euro NCAP, IIHS, JNCAP) | 30,000 |

**Edge tables** (9):

| Edge | src → dst | semantic |
|---|---|---|
| `edge_kuruma_model_by_maker` | model → maker (= vertex_legal_entity) | 製造元 |
| `edge_kuruma_uses_platform` | model → platform | プラットフォーム共有 |
| `edge_kuruma_contains_part` | model → part | BOM |
| `edge_kuruma_part_supplier` | part → supplier (= vertex_legal_entity) | Tier 1/2 調達先 |
| `edge_kuruma_assembled_at` | unit → plant | 生産拠点 |
| `edge_kuruma_unit_model` | unit → model | VIN → モデル |
| `edge_kuruma_sold_by` | unit → dealer (= vertex_legal_entity) | 販売店 |
| `edge_kuruma_has_feature` | model → feature | 装備搭載 |
| `edge_kuruma_recall_affects` | recall → model | 対象モデル |

**Streaming MVs** (5):

- `mv_kuruma_supply_chain_depth` — model × max(tier) via transitive edge_kuruma_part_supplier
- `mv_kuruma_sales_by_country` — model × country × year × sum(volume)
- `mv_kuruma_dealer_density` — country × count(dealer) / population
- `mv_kuruma_platform_share` — platform × model_count / model_total
- `mv_kuruma_recall_per_maker` — maker × recall_count × affected_unit_count

### B. media_anime — アニメドメイン深さ設計

13 vertex + 11 edge + 5 MV。制作委員会構造・配信ネットワークを追跡。

**Path DID 階層**:
```
did:web:media-anime.etzhayyim.com
did:web:media-anime.etzhayyim.com:title:{mal-or-anilist-id}    — 作品
did:web:media-anime.etzhayyim.com:franchise:{qid}              — シリーズ / IP 全体
did:web:media-anime.etzhayyim.com:studio:{qid}                 — 制作スタジオ
did:web:media-anime.etzhayyim.com:committee:{title-id}         — 製作委員会
did:web:media-anime.etzhayyim.com:staff:{qid}                  — 監督・脚本・作画・声優
did:web:media-anime.etzhayyim.com:character:{title}:{slug}     — キャラクター
did:web:media-anime.etzhayyim.com:episode:{title}:{ep-number}  — エピソード
did:web:media-anime.etzhayyim.com:broadcaster:{qid}            — TV 局・配信プラットフォーム
did:web:media-anime.etzhayyim.com:distribution:{title}:{country}:{platform} — 配信契約
did:web:media-anime.etzhayyim.com:source:{type}:{id}           — 原作 (manga/LN/game)
did:web:media-anime.etzhayyim.com:song:{title}:{kind}:{n}      — OP/ED/BGM
did:web:media-anime.etzhayyim.com:merchandise:{title}:{sku}    — グッズ
```

**Vertex tables** (13):

| Table | Scope | world_total 推定 |
|---|---|---|
| `vertex_anime_title` | 作品 (=media_anime, existing) | 25,000 |
| `vertex_anime_franchise` | IP / シリーズ | 5,000 |
| `vertex_anime_studio` | 制作スタジオ | 500 |
| `vertex_anime_committee` | 製作委員会 | 15,000 (≒ title × 0.6) |
| `vertex_anime_staff` | 監督・脚本・作画・声優 | 100,000 |
| `vertex_anime_character` | キャラクター | 500,000 (20/title) |
| `vertex_anime_episode` | エピソード | 500,000 |
| `vertex_anime_broadcaster` | TV/streaming platform | 2,000 |
| `vertex_anime_distribution` | 配信契約 (title × country × platform) | 500,000 |
| `vertex_anime_source` | 原作 (manga/LN/game) | 15,000 |
| `vertex_anime_song` | OP/ED/BGM | 100,000 (4/title) |
| `vertex_anime_merchandise` | グッズ | 5,000,000 |
| `vertex_anime_ratings` | 視聴率・評価 | 100,000 |

**Edge tables** (11):

| Edge | src → dst | semantic |
|---|---|---|
| `edge_anime_produced_by` | title → studio | 制作 |
| `edge_anime_funded_by` | title → committee | 制作委員会出資 |
| `edge_anime_committee_member` | committee → legal_entity | 委員会参加企業 |
| `edge_anime_part_of_franchise` | title → franchise | シリーズ帰属 |
| `edge_anime_stars_character` | title → character | 登場キャラ |
| `edge_anime_voiced_by` | character → staff | 声優担当 |
| `edge_anime_directed_by` | title → staff | 監督・制作スタッフ |
| `edge_anime_aired_on` | title → broadcaster | 放送局 |
| `edge_anime_licensed_to` | title → distribution | 配信先 |
| `edge_anime_adapted_from` | title → source | 原作参照 |
| `edge_anime_has_song` | title → song | OP/ED |

**Streaming MVs** (5):

- `mv_anime_studio_production_count` — studio × count(title × year)
- `mv_anime_distribution_by_country` — country × count(distinct title) (配信到達度)
- `mv_anime_character_depth` — title × count(character) (キャラ充実度)
- `mv_anime_committee_network` — legal_entity (partner) × count(committee) (委員会常連度)
- `mv_anime_source_adaptation_ratio` — source_type × adapted_count / total_count

### C. media_gamers — ビデオゲームドメイン深さ設計

14 vertex + 12 edge + 6 MV。プラットフォーム / エンジン / 流通 / esports を追跡。

**Path DID 階層**:
```
did:web:media-gamers.etzhayyim.com
did:web:media-gamers.etzhayyim.com:title:{igdb-or-steam-id}
did:web:media-gamers.etzhayyim.com:franchise:{qid}
did:web:media-gamers.etzhayyim.com:platform:{qid}             — PS5/Switch/PC
did:web:media-gamers.etzhayyim.com:engine:{qid}               — Unity/Unreal/Godot
did:web:media-gamers.etzhayyim.com:store:{qid}                — Steam/Epic/eShop
did:web:media-gamers.etzhayyim.com:developer:{lei-or-qid}     → vertex_legal_entity
did:web:media-gamers.etzhayyim.com:publisher:{lei-or-qid}     → vertex_legal_entity
did:web:media-gamers.etzhayyim.com:character:{title}:{slug}
did:web:media-gamers.etzhayyim.com:map:{title}:{slug}
did:web:media-gamers.etzhayyim.com:item:{title}:{slug}
did:web:media-gamers.etzhayyim.com:quest:{title}:{slug}       — ストーリ/クエスト
did:web:media-gamers.etzhayyim.com:dlc:{title}:{slug}
did:web:media-gamers.etzhayyim.com:sales:{title}:{region}:{ym}
did:web:media-gamers.etzhayyim.com:esports:{event-id}
```

**Vertex tables** (14):

| Table | Scope | world_total 推定 |
|---|---|---|
| `vertex_game_title` | ゲーム (=media_gamers, existing) | 900,000 |
| `vertex_game_franchise` | シリーズ | 30,000 |
| `vertex_game_platform` | ハードウェア | 200 |
| `vertex_game_engine` | エンジン | 1,000 |
| `vertex_game_store` | 流通ストア | 50 |
| `vertex_game_character` | キャラクター | 10,000,000 |
| `vertex_game_map` | マップ/レベル | 5,000,000 |
| `vertex_game_item` | アイテム | 50,000,000 |
| `vertex_game_quest` | クエスト/ストーリ | 10,000,000 |
| `vertex_game_dlc` | 拡張/DLC | 500,000 |
| `vertex_game_sales_monthly` | 月次販売 | 10,000,000 rows/year |
| `vertex_game_esports_event` | esports 大会 | 50,000 |
| `vertex_game_genre` | ジャンル | 500 |
| `vertex_game_mode` | プレイモード (single/multi/MMO) | 100 |

**Edge tables** (12):

| Edge | src → dst | semantic |
|---|---|---|
| `edge_game_developed_by` | title → developer (vertex_legal_entity) | 開発元 |
| `edge_game_published_by` | title → publisher (vertex_legal_entity) | 販売元 |
| `edge_game_runs_on` | title → platform | 対応ハード |
| `edge_game_uses_engine` | title → engine | エンジン |
| `edge_game_sold_on` | title → store | 流通先 |
| `edge_game_has_character` | title → character | 登場キャラ |
| `edge_game_has_map` | title → map | マップ所属 |
| `edge_game_has_item` | title → item | アイテム所属 |
| `edge_game_has_quest` | title → quest | クエスト所属 |
| `edge_game_part_of_franchise` | title → franchise | シリーズ |
| `edge_game_has_genre` | title → genre | ジャンル分類 |
| `edge_game_esports_for` | esports_event → title | 競技種目 |

**Streaming MVs** (6):

- `mv_game_platform_share` — platform × count(title)
- `mv_game_engine_usage` — engine × count(title)
- `mv_game_sales_by_region` — region × sum(volume)
- `mv_game_character_depth` — title × count(character)
- `mv_game_franchise_lifecycle` — franchise × first_year × last_year × count(title)
- `mv_game_esports_per_genre` — genre × count(esports_event)

## Coverage evaluation formula

per-subdomain coverage rate = `count(vertex_<domain>_<sub>) / world_total_estimate`

`mv_<domain>_sub_coverage` を 3 ドメイン分追加し、`mv_world_coverage_live` と左 JOIN して `etzhayyim coverage world --depth` で表示:

```
DOMAIN            COLLECTED    WORLD_TOTAL   COVERAGE    SUB-DEPTH
kuruma              4,970       80,000        6.21%      3/12 sub-vertex populated
media_anime        25,000       25,000      100.00%      1/13 sub-vertex populated
media_gamers       10,000      900,000        1.11%      1/14 sub-vertex populated
```

## Rationale

### Why 11-axis (法人/製作者/キャラクター/マップ/アイテム/部品/ストーリ/取引先/販売台数/流通台数/国別)

これらはドメインに依存しない**ドメイン知識グラフの canonical 軸**:

| 軸 | kuruma | anime | gamers |
|---|---|---|---|
| 法人 | maker / supplier / dealer | studio / broadcaster / committee-member | developer / publisher / store |
| 製作者 | (engineer = staff optional) | staff (director/animator/VA) | staff (programmer/artist/composer) |
| キャラクター | — | character | character |
| マップ | — | — | map |
| アイテム | feature / trim | merchandise | item / dlc |
| 部品 | part | — | (not meaningful) |
| ストーリ | — | episode | quest |
| 取引先 | supplier / dealer | committee_member | — |
| 販売台数 | sales_monthly | — | sales_monthly |
| 流通台数 | unit (VIN) | distribution | store × title |
| 国別 | sales × country | distribution × country | sales × region |

欠落 (—) は semantic 不成立。

### Why vertex + edge separation (not denormalized)

- **Kotoba/Datomic streaming MV** は edge 型式の方が `COUNT(DISTINCT src_vid)` 集計が安価 (index-scan 1 方向)
- **P10v2 promoted columns** 原則: 1 row = 1 entity。edge は relation artifact なので `src_vid/dst_vid` PK で圧縮
- AT Protocol commit pipeline: vertex と edge を別 NSID collection にすることで PDS の record-size limit (1 MB) 回避

## Exceptions

- **parts (10M)** と **units (1.5B)** は超巨大。単一 Kotoba/Datomic node でホストしきれない → 将来 **Iceberg S3 Parquet cold tier** へ分離 (ADR 0002 `Iceberg archive` 参照)
- **character (10M for games)** と **item (50M)** は IGDB/VNDB 等の有料 API が source → Phase 3 で段階導入

## References

- `30-graph/graph-schema/migrations/0045_vertex_kuruma_depth.ts` — 実装
- `30-graph/graph-schema/migrations/0046_vertex_anime_depth.ts` — 実装
- `30-graph/graph-schema/migrations/0047_vertex_game_depth.ts` — 実装
- `30-graph/graph-schema/migrations/0025_world_coverage_live_mv.ts` — 親 MV
- ADR 0002 persistence-kotoba-only
- ADR 0019 atproto-native-identifier-topology
