import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: A  (3D blob catalog — public dataset metadata + B2 keys.
//          Body content (STEP / STL / OBJ / voxel grid blobs) is on B2,
//          not in this row. Catalog is fully shareable across orgs.)

/**
 * vertex_3d_blob — ADSK Phase 2 catalog of 3D dataset samples
 * (ABC-1M / Make-A-Shape / WaLa) ingested to B2.
 *
 * Phase 1 (2026-05-05) handled text/code datasets only into
 * `vertex_hf_dataset_record`. Phase 2 (this migration) introduces a
 * separate catalog for 3D blob samples because:
 *
 *   - 3D blobs are too large to inline (STEP/STL ≥ 100 KB / sample,
 *     ABC-1M total ~7 TiB) — they MUST live in B2.
 *   - The catalog row stores B2 location + sha256 + format only.
 *   - voxelforge LangGraph `route_generator` node may reference this
 *     catalog as a few-shot retrieval store for CAD samples.
 *
 * Sources (Phase 2 scope):
 *   abc1m         ABC-1M  — 1M CAD STEP files (Microsoft / NYU)
 *   make_a_shape  Make-A-Shape — voxel grids for shape gen
 *   wala          WaLa  — latent codes for shape gen
 *   internal      Operator-uploaded sample (e.g., reference building)
 *
 * Content-addressed PK (ADR-0041): sha256(source + slug + sample_id).
 *
 * Streaming MV: mv_3d_blob_count_by_source — narrow GROUP BY on
 * (source, format, day). Bounded ~16 keys × 365d ≈ 6K rows.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_3d_blob (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      source varchar NOT NULL,
      slug varchar NOT NULL,
      sample_id varchar NOT NULL,
      format varchar NOT NULL,
      b2_bucket varchar NOT NULL,
      b2_key varchar NOT NULL,
      sha256_hex varchar NOT NULL,
      byte_size bigint NOT NULL,
      polygon_count bigint,
      voxel_dim int,
      latent_dim int,
      license varchar,
      hf_url varchar,
      ts_ms bigint NOT NULL,
      ingested_by_run_id varchar,
      actor_did varchar NOT NULL,
      org_did varchar NOT NULL,
      at_did varchar,
      created_at varchar NOT NULL,
      org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_3d_blob_source ON vertex_3d_blob (source, ts_ms)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_3d_blob_slug ON vertex_3d_blob (slug, sample_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_3d_blob_format ON vertex_3d_blob (format, source)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_3d_blob_count_by_source AS
      SELECT
        source,
        format,
        CAST(to_timestamp(ts_ms / 1000.0) AS date) AS day,
        COUNT(*) AS sample_count,
        SUM(byte_size) AS total_byte_size
      FROM vertex_3d_blob
      GROUP BY source, format, CAST(to_timestamp(ts_ms / 1000.0) AS date);
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_3d_blob_count_by_source`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_3d_blob`.execute(db);
}
