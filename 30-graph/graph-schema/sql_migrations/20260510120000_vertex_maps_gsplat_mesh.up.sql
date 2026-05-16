-- ADR 2605092800 §D6 — bake-mesh registry for splat→mesh lineage.
--
-- One row per baked GLB. The lineage edge `edge_maps_gsplat_baked_to`
-- (added in `20260509220000_vertex_maps_gsplat_asset.up.sql`) joins
-- this mesh row's `vertex_id` to the source splat asset's
-- `vertex_id` so consumers can either:
--   1. start from a tile_h3 and find both splat + mesh, or
--   2. start from a splat row and resolve its baked mesh.
--
-- Persistence model = "Record-log semantics": no ON CONFLICT,
-- PK re-INSERT = implicit upsert. Append-only. The bake worker
-- re-INSERTs the row keyed on `vertex_id` if a re-bake happens.
--
-- Sensitivity: Tier 1 — mesh GLBs are derived from public street
-- imagery; metadata is graph-public.

CREATE TABLE IF NOT EXISTS vertex_maps_gsplat_mesh (
  vertex_id          varchar PRIMARY KEY,
  _seq               bigint,
  created_date       date,
  sensitivity_ord    bigint DEFAULT 1,
  owner_did          varchar,
  gsplat_vertex_id   varchar NOT NULL,
  tile_h3            varchar NOT NULL,
  bake_job_id        varchar,
  b2_key             varchar NOT NULL,
  byte_size          bigint  NOT NULL,
  triangle_count     bigint  NOT NULL,
  view_count         int,
  bake_runtime_ms    bigint,
  baker_version      varchar,
  baked_at           varchar NOT NULL,
  props              varchar,
  actor_did          varchar NOT NULL DEFAULT 'anon',
  org_did            varchar NOT NULL DEFAULT 'anon',
  at_did             varchar,
  created_at         varchar NOT NULL DEFAULT '1970-01-01T00:00:00Z'
);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_mesh_tile
  ON vertex_maps_gsplat_mesh (tile_h3, baked_at DESC);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_mesh_gsplat
  ON vertex_maps_gsplat_mesh (gsplat_vertex_id);

CREATE INDEX IF NOT EXISTS idx_maps_gsplat_mesh_bake_job
  ON vertex_maps_gsplat_mesh (bake_job_id);
