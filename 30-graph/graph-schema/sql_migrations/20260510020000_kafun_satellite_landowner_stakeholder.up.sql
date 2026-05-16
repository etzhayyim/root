-- Kafun real-world outreach pipeline: satellite tile → canopy → cadastral parcel
-- → landowner → stakeholder. Seeds 主要日本組織 (中央省庁 + 林業 + 研究 + 患者団体
-- + 大手林業民間) + 4 sub-DAG topo nodes.
--
-- Path of an action:
--   vertex_kafun_satellite_tile (capture)
--   ↓ edge_kafun_canopy_in_tile
--   vertex_kafun_canopy_segment (sugi/hinoki polygon, ML-detected)
--   ↓ edge_kafun_canopy_in_parcel
--   vertex_kafun_cadastral_parcel (法務省登記 / MLIT 国土数値情報)
--   ↓ edge_kafun_parcel_owned_by
--   vertex_kafun_landowner (国・都道府県・市町村・森林組合・法人・自然人)
--   ↓ edge_kafun_landowner_member_of
--   vertex_kafun_stakeholder (森林組合連合会 / 林野庁 等)
--   ↓ edge_kafun_outreach_sent_to
--   vertex_kafun_action (envoy DID 経由の outreach)
--
-- Persistence: record-log semantics. RW: no JSONB, no ON CONFLICT.

-- ─────────────────────────────────────────────────────────────────────────
-- Satellite & canopy detection
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_kafun_satellite_tile (
  vertex_id        varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  provider         varchar NOT NULL,        -- copernicus_sentinel2 | jaxa_alos | aster | planet_labs
  scene_id         varchar,                 -- provider scene/granule id
  capture_at       varchar NOT NULL,        -- ISO 8601
  capture_year     bigint NOT NULL,
  bbox_min_lon     double precision,
  bbox_min_lat     double precision,
  bbox_max_lon     double precision,
  bbox_max_lat     double precision,
  cloud_cover_pct  double precision,
  resolution_m     double precision,
  blob_key         varchar,                 -- B2 / R2 key for the raster
  ingested_at      varchar
);
CREATE INDEX IF NOT EXISTS idx_satellite_tile_capture ON vertex_kafun_satellite_tile (capture_year, provider);
CREATE INDEX IF NOT EXISTS idx_satellite_tile_bbox    ON vertex_kafun_satellite_tile (bbox_min_lat, bbox_min_lon);

CREATE TABLE IF NOT EXISTS vertex_kafun_canopy_segment (
  vertex_id           varchar PRIMARY KEY,
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 0,
  owner_did           varchar,
  source_tile_id      varchar NOT NULL,      -- → vertex_kafun_satellite_tile
  prefecture          varchar,
  municipality        varchar,
  centroid_lon        double precision,
  centroid_lat        double precision,
  area_ha             double precision,
  geom_geojson        varchar,
  species_pred        varchar,                -- sugi | hinoki | mixed | unknown
  confidence          double precision DEFAULT 0,
  detector_model      varchar,
  detected_at         varchar,
  parcel_resolved_at  varchar                -- NULL = unattributed; set when edge_canopy_in_parcel created
);
CREATE INDEX IF NOT EXISTS idx_canopy_pref_species  ON vertex_kafun_canopy_segment (prefecture, species_pred);
CREATE INDEX IF NOT EXISTS idx_canopy_unattributed  ON vertex_kafun_canopy_segment (parcel_resolved_at, area_ha);

CREATE TABLE IF NOT EXISTS edge_kafun_canopy_in_tile (
  edge_id          varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  src_vid          varchar NOT NULL,         -- canopy
  dst_vid          varchar NOT NULL,         -- tile
  created_at       varchar
);
CREATE INDEX IF NOT EXISTS idx_canopy_in_tile_src ON edge_kafun_canopy_in_tile (src_vid);
CREATE INDEX IF NOT EXISTS idx_canopy_in_tile_dst ON edge_kafun_canopy_in_tile (dst_vid);

-- ─────────────────────────────────────────────────────────────────────────
-- Cadastral / landowner
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_kafun_cadastral_parcel (
  vertex_id           varchar PRIMARY KEY,   -- e.g. 'jpn:13:111:0001:xxxx'
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 0,
  owner_did           varchar,
  source              varchar NOT NULL,      -- mlit_kokudo | houmusyo_touki | mof_keieikiban | citizen
  prefecture          varchar NOT NULL,      -- ISO 3166-2:JP code (JP-13 etc.)
  city_code           varchar,               -- 全国地方公共団体コード
  oaza                varchar,
  chiban              varchar,               -- 地番
  area_m2             double precision,
  centroid_lon        double precision,
  centroid_lat        double precision,
  geom_geojson        varchar,
  registry_book_kind  varchar,               -- 国 | 都道府県 | 市町村 | 民有
  lookup_at           varchar
);
CREATE INDEX IF NOT EXISTS idx_parcel_pref_city  ON vertex_kafun_cadastral_parcel (prefecture, city_code);
CREATE INDEX IF NOT EXISTS idx_parcel_book_kind  ON vertex_kafun_cadastral_parcel (registry_book_kind);

CREATE TABLE IF NOT EXISTS vertex_kafun_landowner (
  vertex_id           varchar PRIMARY KEY,
  _seq                bigint,
  created_date        date,
  sensitivity_ord     bigint DEFAULT 1,      -- private-person rows higher
  owner_did           varchar,
  owner_kind          varchar NOT NULL,      -- national | prefecture | municipality | forest_coop | legal_entity | natural_person | unknown
  name                varchar,                -- public name; for natural persons store hash only
  legal_entity_lei    varchar,                -- → vertex_legal_entity if applicable
  jurisdiction_iso    varchar,                -- ISO 3166-2:JP code if local government
  address_pref        varchar,
  contact_email       varchar,
  contact_status      varchar DEFAULT 'unreachable',  -- unreachable | reachable | in_dialogue | agreement_signed | declined
  parcel_count        bigint DEFAULT 0,       -- maintained by mv_kafun_landowner_parcel_count (advisory)
  total_area_ha       double precision DEFAULT 0,
  last_contacted_at   varchar,
  created_at          varchar
);
CREATE INDEX IF NOT EXISTS idx_landowner_kind     ON vertex_kafun_landowner (owner_kind, contact_status);
CREATE INDEX IF NOT EXISTS idx_landowner_lei      ON vertex_kafun_landowner (legal_entity_lei);
CREATE INDEX IF NOT EXISTS idx_landowner_jur      ON vertex_kafun_landowner (jurisdiction_iso);

CREATE TABLE IF NOT EXISTS edge_kafun_canopy_in_parcel (
  edge_id          varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  src_vid          varchar NOT NULL,         -- canopy
  dst_vid          varchar NOT NULL,         -- parcel
  intersection_ha  double precision DEFAULT 0,
  resolved_at      varchar
);
CREATE INDEX IF NOT EXISTS idx_canopy_in_parcel_src ON edge_kafun_canopy_in_parcel (src_vid);
CREATE INDEX IF NOT EXISTS idx_canopy_in_parcel_dst ON edge_kafun_canopy_in_parcel (dst_vid);

CREATE TABLE IF NOT EXISTS edge_kafun_parcel_owned_by (
  edge_id          varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  src_vid          varchar NOT NULL,         -- parcel
  dst_vid          varchar NOT NULL,         -- landowner
  share_pct        double precision DEFAULT 100,  -- joint ownership share
  recorded_at      varchar
);
CREATE INDEX IF NOT EXISTS idx_parcel_owned_src ON edge_kafun_parcel_owned_by (src_vid);
CREATE INDEX IF NOT EXISTS idx_parcel_owned_dst ON edge_kafun_parcel_owned_by (dst_vid);

-- ─────────────────────────────────────────────────────────────────────────
-- Stakeholders (政府・団体・組合・学会・民間)
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS vertex_kafun_stakeholder (
  vertex_id              varchar PRIMARY KEY,
  _seq                   bigint,
  created_date           date,
  sensitivity_ord        bigint DEFAULT 0,
  owner_did              varchar,
  kind                   varchar NOT NULL,
    -- ministry | central_agency | prefecture_dept | municipality_dept |
    -- forest_coop_fed | forest_coop | industry_assoc | patient_group |
    -- academic_society | research_institute | private_corp | political | media
  name                   varchar NOT NULL,
  name_en                varchar,
  jurisdiction_iso       varchar,             -- JP-13 etc, or 'JP' for national
  parent_stakeholder_id  varchar,             -- hierarchical (省 → 局 → 課)
  role_in_dag            varchar,             -- which topo_node category they affect
  legal_entity_lei       varchar,
  website                varchar,
  contact_email          varchar,
  contact_phone          varchar,
  contact_status         varchar DEFAULT 'unreachable',
  last_contacted_at      varchar,
  created_at             varchar
);
CREATE INDEX IF NOT EXISTS idx_stakeholder_kind ON vertex_kafun_stakeholder (kind, jurisdiction_iso);
CREATE INDEX IF NOT EXISTS idx_stakeholder_jur  ON vertex_kafun_stakeholder (jurisdiction_iso, contact_status);
CREATE INDEX IF NOT EXISTS idx_stakeholder_role ON vertex_kafun_stakeholder (role_in_dag);

CREATE TABLE IF NOT EXISTS edge_kafun_landowner_member_of (
  edge_id          varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  src_vid          varchar NOT NULL,         -- landowner
  dst_vid          varchar NOT NULL,         -- stakeholder (forest_coop)
  joined_at        varchar
);
CREATE INDEX IF NOT EXISTS idx_lo_member_src ON edge_kafun_landowner_member_of (src_vid);
CREATE INDEX IF NOT EXISTS idx_lo_member_dst ON edge_kafun_landowner_member_of (dst_vid);

-- envoy が打った outreach。dst は landowner OR stakeholder のいずれか。
CREATE TABLE IF NOT EXISTS edge_kafun_outreach_sent_to (
  edge_id          varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 0,
  owner_did        varchar,
  src_vid          varchar NOT NULL,         -- vertex_kafun_action
  dst_vid          varchar NOT NULL,         -- landowner OR stakeholder
  channel          varchar NOT NULL,         -- email | letter | meeting | xrpc | bsky_post
  envoy_actor_did  varchar,
  yoro_post_uri    varchar,                  -- mirror post URI for transparency
  status           varchar DEFAULT 'sent',   -- sent | delivered | replied | declined | timeout
  sent_at          varchar
);
CREATE INDEX IF NOT EXISTS idx_outreach_dst    ON edge_kafun_outreach_sent_to (dst_vid, status);
CREATE INDEX IF NOT EXISTS idx_outreach_envoy  ON edge_kafun_outreach_sent_to (envoy_actor_did, sent_at);

-- ─────────────────────────────────────────────────────────────────────────
-- MVs
-- ─────────────────────────────────────────────────────────────────────────

-- 検出されたが parcel に紐付いていない canopy 合計 (47県別)。
-- cardinality bounded by prefecture (47); safe streaming MV.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kafun_unattributed_canopy AS
SELECT prefecture,
       species_pred,
       SUM(area_ha) AS unattributed_ha,
       COUNT(*)     AS segment_count
FROM   vertex_kafun_canopy_segment
WHERE  parcel_resolved_at IS NULL
GROUP  BY prefecture, species_pred;

-- Landowner outreach funnel by (kind × contact_status).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kafun_owner_outreach_funnel AS
SELECT owner_kind,
       contact_status,
       COUNT(*)             AS owner_count,
       SUM(parcel_count)    AS parcel_total,
       SUM(total_area_ha)   AS area_total_ha
FROM   vertex_kafun_landowner
GROUP  BY owner_kind, contact_status;

-- Stakeholder coverage by jurisdiction × kind (47 prefs × ~12 kinds = 564 max rows).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kafun_stakeholder_coverage AS
SELECT jurisdiction_iso,
       kind,
       COUNT(*)                                                    AS total,
       COUNT(*) FILTER (WHERE contact_status = 'in_dialogue')       AS in_dialogue,
       COUNT(*) FILTER (WHERE contact_status = 'agreement_signed')  AS agreed,
       COUNT(*) FILTER (WHERE contact_status = 'declined')          AS declined,
       COUNT(*) FILTER (WHERE contact_status = 'unreachable')       AS unreachable
FROM   vertex_kafun_stakeholder
GROUP  BY jurisdiction_iso, kind;

-- Per-(prefecture, year) canopy detection rollup.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kafun_canopy_pref_year AS
SELECT c.prefecture,
       SUBSTR(c.detected_at, 1, 4) AS detected_year,
       c.species_pred,
       SUM(c.area_ha)             AS area_ha,
       COUNT(*)                   AS segment_count
FROM   vertex_kafun_canopy_segment c
GROUP  BY c.prefecture, SUBSTR(c.detected_at, 1, 4), c.species_pred;
