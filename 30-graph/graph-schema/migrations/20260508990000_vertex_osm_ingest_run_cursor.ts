import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration: OSM ingest run tracking + mid-run cursor + B2 PBF cache.
 *
 * Three tables that form the operational backbone of the OSM PBF ingest
 * pipeline (`70-tools/maps-osm-ingest` or equivalent pyzeebe primitives):
 *
 *   - `vertex_osm_ingest_run`    — one row per ingest execution, lifecycle
 *     from 'init' → 'download' → 'node' → 'way' → 'rel' → 'done'.
 *     Tracks byte-level provenance (pbf_url / pbf_b2_key / pbf_sha256 /
 *     pbf_size_bytes) and throughput (rows_per_sec).
 *
 *   - `vertex_osm_ingest_cursor` — mid-run progress per (run_id, phase).
 *     Written every BATCH_SIZE rows so a crashed ingest can resume from
 *     the last flushed cursor instead of re-downloading the PBF.
 *     PK = '{run_id}:{phase}' (upsert via delete-then-insert per
 *     delete-then-insert upsert (no native conflict clause in RisingWave).
 *
 *   - `vertex_osm_pbf_cache`     — B2 object key for each Geofabrik daily
 *     PBF that has been downloaded + verified. Cache hit avoids a 800 MB+
 *     re-download on repeated ingests. PK = '{source_did}:{date_str}'.
 *
 * RisingWave notes:
 *   - `DEFAULT uuid_generate_v4()` is NOT supported; UUIDs generated in app.
 *   - `DEFAULT now()` / `DEFAULT CURRENT_TIMESTAMP` are NOT supported on
 *     TIMESTAMPTZ columns in RisingWave; timestamps set by app.
 *   - `DOUBLE PRECISION` is supported and used for rows_per_sec.
 *   - No ON CONFLICT; idempotent upsert = delete-then-insert pattern.
 *   - No db.transaction() (RW write-TX not supported).
 *
 * Source provenance: `source_did` = e.g. 'did:web:maps.gftd.ai:planet'
 * or a region-scoped sub-DID such as 'did:web:maps.gftd.ai:planet:jp'.
 *
 * Streaming MV: `mv_osm_ingest_recent` surfaces the last N runs ordered
 * by started_at DESC for the `/coverage` XRPC and the Zeebe audit handler.
 * Cardinality bound: total run count is bounded by ingest cadence (daily at
 * most) × region count (< 200). No GROUP BY; full-scan MV is safe.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_osm_ingest_run ─────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_osm_ingest_run (
      run_id           VARCHAR PRIMARY KEY,
      source_did       VARCHAR NOT NULL,
      pbf_url          VARCHAR,
      pbf_b2_key       VARCHAR,
      pbf_sha256       VARCHAR,
      pbf_size_bytes   BIGINT,
      started_at       TIMESTAMPTZ NOT NULL,
      completed_at     TIMESTAMPTZ,
      phase            VARCHAR NOT NULL DEFAULT 'init',
      nodes_total      BIGINT,
      ways_total       BIGINT,
      rels_total       BIGINT,
      nodes_written    BIGINT NOT NULL DEFAULT 0,
      ways_written     BIGINT NOT NULL DEFAULT 0,
      rel_rows_written BIGINT NOT NULL DEFAULT 0,
      rows_per_sec     DOUBLE PRECISION,
      status           VARCHAR NOT NULL DEFAULT 'running',
      error_msg        VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_run_source_did ON vertex_osm_ingest_run (source_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_run_status ON vertex_osm_ingest_run (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_run_started_at ON vertex_osm_ingest_run (started_at)`.execute(db);

  // ── vertex_osm_ingest_cursor ──────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_osm_ingest_cursor (
      cursor_id    VARCHAR PRIMARY KEY,
      run_id       VARCHAR NOT NULL,
      source_did   VARCHAR NOT NULL,
      phase        VARCHAR NOT NULL,
      rows_written BIGINT NOT NULL DEFAULT 0,
      last_osm_id  BIGINT,
      updated_at   TIMESTAMPTZ NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_cursor_run_id ON vertex_osm_ingest_cursor (run_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_cursor_source_did ON vertex_osm_ingest_cursor (source_did)`.execute(db);

  // ── vertex_osm_pbf_cache ──────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_osm_pbf_cache (
      cache_id       VARCHAR PRIMARY KEY,
      source_did     VARCHAR NOT NULL,
      geofabrik_url  VARCHAR NOT NULL,
      b2_key         VARCHAR NOT NULL,
      size_bytes     BIGINT NOT NULL,
      sha256         VARCHAR NOT NULL,
      cached_at      TIMESTAMPTZ NOT NULL,
      last_used_at   TIMESTAMPTZ NOT NULL,
      valid_date     VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_osm_pbf_cache_source_did ON vertex_osm_pbf_cache (source_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_pbf_cache_valid_date ON vertex_osm_pbf_cache (valid_date)`.execute(db);

  // ── mv_osm_ingest_recent (narrow streaming MV) ────────────────────────
  // Cardinality: bounded by (ingest_cadence × region_count) ≪ 10K rows.
  // No GROUP BY, no MAX(varchar) → safe per MV memory guardrail.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_osm_ingest_recent AS
    SELECT
      run_id,
      source_did,
      phase,
      status,
      nodes_written,
      ways_written,
      rows_per_sec,
      started_at,
      completed_at
    FROM vertex_osm_ingest_run
    ORDER BY started_at DESC
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_osm_ingest_recent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_osm_pbf_cache`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_osm_ingest_cursor`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_osm_ingest_run`.execute(db);
}
