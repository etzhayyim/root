import type { Kysely } from "kysely";
import { sql } from "kysely";

// maps 建物 3D model storage pipeline (ADR-0056 BPMN-as-actor).
//
//   vertex_maps_building_3d     — per-building 3D geometry + source metadata.
//   vertex_maps_building_coverage — per-H3-cell coverage status (sentinel + mapraly).
//
// The buildingIngest3d.bpmn R/PT1H worker populates both tables by:
//   1. Claiming pending H3 res10 cells from vertex_spatial Building rows.
//   2. Computing AABB extents from centroid lat/lng + footprint.
//   3. Noting which cells have Sentinel imagery coverage.
//   4. Upserting coverage summaries into vertex_maps_building_coverage.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps_building_3d (
      vertex_id         VARCHAR PRIMARY KEY,
      spatial_vertex_id VARCHAR,
      tile_h3           VARCHAR NOT NULL,
      h3_resolution     BIGINT,
      centroid_lat      DOUBLE PRECISION,
      centroid_lng      DOUBLE PRECISION,
      footprint_json    VARCHAR,
      height_m          DOUBLE PRECISION,
      source            VARCHAR NOT NULL,
      mesh_uri          VARCHAR,
      coverage_score    DOUBLE PRECISION,
      ingest_at         VARCHAR,
      created_at        VARCHAR,
      sensitivity_ord   BIGINT,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      owner_did         VARCHAR,
      _seq              BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_building_3d_tile_h3
      ON vertex_maps_building_3d (tile_h3)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_building_3d_spatial_vid
      ON vertex_maps_building_3d (spatial_vertex_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_building_3d_source
      ON vertex_maps_building_3d (source, ingest_at)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps_building_coverage (
      vertex_id         VARCHAR PRIMARY KEY,
      tile_h3           VARCHAR NOT NULL,
      h3_resolution     BIGINT,
      centroid_lat      DOUBLE PRECISION,
      centroid_lng      DOUBLE PRECISION,
      building_count    BIGINT,
      has_sentinel      BOOLEAN,
      has_mapraly       BOOLEAN,
      coverage_source   VARCHAR,
      last_ingest_at    VARCHAR,
      status            VARCHAR NOT NULL,
      created_at        VARCHAR,
      sensitivity_ord   BIGINT,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      owner_did         VARCHAR,
      _seq              BIGINT
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_building_coverage_tile
      ON vertex_maps_building_coverage (tile_h3)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps_building_coverage_status
      ON vertex_maps_building_coverage (status, last_ingest_at)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_maps_building_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_maps_building_3d`.execute(db);
}
