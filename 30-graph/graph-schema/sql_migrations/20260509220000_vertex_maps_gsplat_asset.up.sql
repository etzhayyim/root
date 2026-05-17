-- ADR 2605092800 — KAMI Gsplat preview asset registry.
--
-- Persists 3D Gaussian Splat assets fetched / generated for the maps.etzhayyim.com
-- street-level pipeline. Asset binary lives in B2 (`b2_key`); this row holds
-- only metadata. The bake pipeline (k8s pod) extracts a static mesh and
-- back-links via `edge_maps_gsplat_baked_to`.
--
-- Persistence model = root CLAUDE.md "Record-log semantics": no ON CONFLICT,
-- PK re-INSERT = implicit upsert. Append-only.
--
-- Sensitivity: Tier 1 (`sensitivity_ord = 1`). Splat clouds derived from
-- public street imagery; metadata is graph-public. PII filtering is the
-- bake pipeline's responsibility (occluded-pedestrian / license-plate
-- removal happens before the binary lands in B2).

CREATE TABLE IF NOT EXISTS vertex_maps_gsplat_asset (
  vertex_id        varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  bigint DEFAULT 1,
  owner_did        varchar,
  source_did       varchar NOT NULL,
  tile_h3          varchar NOT NULL,
  b2_key           varchar NOT NULL,
  byte_size        bigint NOT NULL,
  splat_count      bigint NOT NULL,
  sh_degree        int NOT NULL DEFAULT 0,
  format           varchar NOT NULL,
  generated_at     varchar NOT NULL,
  bake_job_id      varchar,
  props            varchar,
  actor_did        varchar NOT NULL DEFAULT 'anon',
  org_did          varchar NOT NULL DEFAULT 'anon',
  at_did           varchar,
  created_at       varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_asset_tile
  ON vertex_maps_gsplat_asset (tile_h3);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_asset_source
  ON vertex_maps_gsplat_asset (source_did, generated_at DESC);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_asset_bake_job
  ON vertex_maps_gsplat_asset (bake_job_id);

-- ── edge_maps_gsplat_baked_to ─────────────────────────────────────────────
-- Lineage: gsplat asset → mesh tile produced by the bake pipeline.
-- 1 row per (gsplat_vertex, mesh_vertex) pair. Many gsplats can fan into
-- one mesh tile (multi-resolution photogrammetry source) and one gsplat
-- can produce multiple mesh LODs.

CREATE TABLE IF NOT EXISTS edge_maps_gsplat_baked_to (
  edge_id           varchar PRIMARY KEY,
  src_vid           varchar NOT NULL,
  dst_vid           varchar NOT NULL,
  _seq              bigint,
  created_date      date,
  sensitivity_ord   bigint DEFAULT 1,
  owner_did         varchar,
  baked_at          varchar NOT NULL,
  bake_job_id       varchar,
  mesh_vertex_label varchar,
  triangle_count    bigint,
  actor_did         varchar NOT NULL DEFAULT 'anon',
  org_did           varchar NOT NULL DEFAULT 'anon',
  at_did            varchar,
  created_at        varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_baked_to_src
  ON edge_maps_gsplat_baked_to (src_vid);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_baked_to_dst
  ON edge_maps_gsplat_baked_to (dst_vid);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_baked_to_job
  ON edge_maps_gsplat_baked_to (bake_job_id);
