---
id: adr-2605100100-kafun-bokumetsu-real-world-pipeline
title: kafun-bokumetsu Real-World Outreach Pipeline
status: active
doc_type: adr
topic: kafun-bokumetsu
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - kafun-bokumetsu-pipeline
related:
  - adr-2605100000-agent-goal-dag-schema
  - adr-2605080600-langgraph-server-granian-l3-runtime
supersedes: []
superseded_by: []
---

# ADR-2605100100: kafun-bokumetsu Real-World Outreach Pipeline

**Status**: accepted (2026-05-10)
**Scope**: `60-apps/etzhayyim-project-public-kafun-bokumetsu`
**Depends on**: ADR-2605100000 (agent goal-DAG), ADR-2605080600 (LangGraph
server), ADR-0019 (path-based actor DIDs), ADR-0036 (Hyperdrive direct write).

## Context

Phase 1 (LangGraph chains + 4 T2 tables) gave kafun a research / propose /
tick loop but no link to **real Japanese reality** (forests, owners,
ministries). Phase 2 (agent goal-DAG, ADR-2605100000) gave it dependency
ranking. Without satellite imagery → cadastral resolution → landowner
identification → stakeholder outreach, neither L1-1 (無花粉苗木の量産) nor
L3-1 (主伐再造林スケール 10万 ha/年) — the two real bottlenecks — can
actually move.

## Decision

Add a 5-stage real-world pipeline with one path-based actor DID per stage,
each producing a typed vertex, joined by typed edges, surfaced by
streaming MVs, and seeded with 30 actual Japanese organisations.

### Stages and DIDs

| Stage | actor DID | Reads | Writes |
|---|---|---|---|
| Imagery ingest (L0-1a) | `:actor:scout` | Sentinel-2 / ALOS / ASTER STAC | `vertex_kafun_satellite_tile` |
| Canopy detection (L0-1b) | `:actor:scout` | satellite_tile (B2 raster) | `vertex_kafun_canopy_segment` + `edge_kafun_canopy_in_tile` |
| Parcel resolution (L0-1c) | `:actor:cadastral` | MLIT 国土数値情報 + 法務省登記 | `vertex_kafun_cadastral_parcel` + `edge_kafun_canopy_in_parcel` |
| Landowner resolution (L0-1d) | `:actor:cadastral` | parcel registry, GLEIF LEI | `vertex_kafun_landowner` + `edge_kafun_parcel_owned_by` |
| Stakeholder outreach (L1-0) | `:actor:envoy` | landowner / stakeholder graph | `edge_kafun_outreach_sent_to` (always with `yoro_post_uri`) |

### MVs

- `mv_kafun_unattributed_canopy` — `(prefecture, species_pred)` → ha + count
  where `parcel_resolved_at IS NULL`. Drives the cadastral backlog dashboard.
- `mv_kafun_owner_outreach_funnel` — `(owner_kind, contact_status)` rollup;
  funnel for envoy progress.
- `mv_kafun_stakeholder_coverage` — `(jurisdiction_iso, kind)` × status counts.
- `mv_kafun_canopy_pref_year` — annual canopy detection rate per prefecture.

### Stakeholder seed (30 rows)

Central: 林野庁, 林木育種センター (FFPRI), 環境省, 厚労省, 文科省, 国交省,
内閣府, FFPRI 森林総合研究所, JICA Forestry. Federations: 全森連 + 11
都道府県森林組合連合会 (Tokyo / Kanagawa / Saitama / Chiba / Shizuoka /
Yamanashi / Tochigi / Gunma / Ibaraki / Nagano + 全森連). Industry: 日本林業
協会, 日本CLT協会, 木材総合情報センター. Patient/medical: アレルギー学会,
耳鼻咽喉科学会, 日本花粉症協会. Private: 住友林業, 王子グリーンリソース,
三井物産フォレスト, 中国木材.

`role_in_dag` on each row encodes which topo node categories the
stakeholder influences (e.g. 林野庁 → `capacity:L1-1,execution:L3-1`),
enabling MV joins between `vertex_agent_topo_node` and
`vertex_kafun_stakeholder` for outreach prioritisation.

### Topo DAG extension

5 new nodes inserted under L0-1 / L1: `L0-1a` 衛星画像取り込み, `L0-1b`
canopy 検出, `L0-1c` parcel 紐付け, `L0-1d` landowner 解決, `L1-0`
stakeholder outreach. New deps: linear chain L0-1a → L0-1b → L0-1c → L0-1d
→ L1-0 (all hard); plus L1-1 → L1-0 (soft) and L3-1 → L1-0 (hard) so the
two execution-side bottlenecks are correctly gated on outreach success.

After applying, `mv_agent_topo_ready` head shifted to `L0-1a` (satellite
imagery ingest) — Theory-of-Constraints rank 0 + layer 0 + kpi_weight 0.6,
no upstream prerequisites.

### Privacy boundary

- Natural-person landowners: `vertex_kafun_landowner.name` MUST be a hash
  for `owner_kind='natural_person'` rows; `address_pref` only stores
  prefecture-level granularity. `sensitivity_ord=1` so RLS routes higher.
- Outreach text published to yoro under `:actor:envoy` MUST exclude PII.
  Helper `sendEmailAndPublish` redacts upstream; the public mirror post
  references `dst_vid` (the landowner / stakeholder vertex_id) but not
  contact details.
- `vertex_kafun_stakeholder.contact_email` populated only from public
  listings — never scraped.

### Public-by-default

Every action of every actor (`scout`, `cadastral`, `envoy`, `researcher`,
`proposer`, `executor`) MUST mirror to yoro via `publishToYoro` /
`sendEmailAndPublish` / `publishBlobToYoro`. No off-yoro side effects are
permitted from this app.

## Why not …

- … crawl 法務省 web for owner names? Legal & PII risk. Use 登記情報提供
  サービス (paid, line-item billable, signed audit trail), or skip private
  ownership entirely until L1-0 yields aggregate forest_coop introductions.
- … model parcels via GeoJSON in `value_json`? RW schema convention is
  promoted columns; geom stored as VARCHAR JSON for now, will move to PostGIS
  if/when RW gains geo type support. centroid_lon/lat promoted for index.
- … give every prefecture forest coop federation a separate row at seed
  time? 47 rows * stakeholder churn outweighs benefit; seeded 11 (Kanto +
  major sugi belts) and let `actor:cadastral` lazily insert the rest.

## Consequences

- 9 new T2 tables (4 vertex + 5 edge), 4 new MVs, 19 new indexes,
  2 new path DIDs.
- LangGraph chains for L0-1a..d are not yet implemented — handler stubs
  ride on `Agent.tick` topo dispatch until per-stage chains land.
- ~600 prefecture forest coop unions still un-seeded; `actor:cadastral` must
  bulk-INSERT them before L1-0 outreach can be truly nation-wide.

## Reference

- Schema: `30-graph/graph-schema/sql_migrations/20260510020000_kafun_satellite_landowner_stakeholder.up.sql`
- Seed:   `30-graph/graph-schema/sql_migrations/20260510020100_kafun_seed_stakeholders_and_subdag.up.sql`
- Alembic: `r_20260510020000_kafun_satellite_landowner_stakeholder` (applied 2026-05-10 on live RW)
- App: `60-apps/etzhayyim-project-public-kafun-bokumetsu/appview/.../src/app.ts`
       (5 actor DIDs registered: researcher / proposer / executor / envoy / scout / cadastral)
