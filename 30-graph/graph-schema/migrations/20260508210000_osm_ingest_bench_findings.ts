import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration: extend OSM ingest tracking with bench findings + config history.
 *
 * Builds on `20260508990000_vertex_osm_ingest_run_cursor` to capture not only
 * "what ran" but also "under what RW config" and "what conclusion did the
 * comparison yield". Goal: turn ad-hoc bench notes (CLAUDE.md prose) into
 * queryable graph data so future operators can answer "what is the best
 * ingest config for a 2 GB Japan-class PBF" with one SQL query.
 *
 * Three changes:
 *
 *   1. ALTER `vertex_osm_ingest_run` ADD columns:
 *        bench_variant            VARCHAR  (NULL=production, else 'baseline'
 *                                          / 'flush5000' / 'distributed' / ...)
 *        batch_size               BIGINT
 *        barrier_interval_ms      BIGINT
 *        checkpoint_frequency     BIGINT
 *        distributed_dml_enabled  BOOLEAN
 *        compute_cpu_request_m    BIGINT
 *        compute_memory_request_gi BIGINT
 *        node_phase_seconds       DOUBLE PRECISION
 *        way_phase_seconds        DOUBLE PRECISION
 *        rel_phase_seconds        DOUBLE PRECISION
 *        aggregate_rows_per_sec   DOUBLE PRECISION  (vertices + edges / wallclock)
 *        edges_written            BIGINT
 *
 *   2. NEW `vertex_osm_ingest_finding` — derived insights from bench analysis.
 *        finding_id PK = '{kind}:{slug}:{created_at_unix}'
 *        kind ∈ ('best_config', 'antipattern', 'observation', 'config_change')
 *        evidence_run_ids = comma-separated list of run_ids
 *        recommended_config = VARCHAR JSON
 *
 *   3. NEW `edge_osm_run_versus` — pairwise bench comparisons.
 *        edge_id PK = '{baseline_run_id}::{variant_run_id}'
 *        speedup_ratio = variant_rps / baseline_rps
 *        speedup_pct = (variant_rps - baseline_rps) / baseline_rps * 100
 *
 *   4. NEW MV `mv_osm_ingest_top_runs` — runs ordered by aggregate_rows_per_sec
 *      DESC (excludes failed/cancelled runs). Narrow projection, status='completed'
 *      only, no GROUP BY → safe streaming MV. Replaces the existing recent MV.
 *
 * RisingWave notes:
 *   - ALTER TABLE ADD COLUMN IF NOT EXISTS supported.
 *   - DEFAULT now() NOT supported on TIMESTAMPTZ; timestamps set by app.
 *   - DOUBLE PRECISION supported.
 *   - VARCHAR JSON (no JSONB).
 *   - No ON CONFLICT; idempotent upsert = delete-then-insert pattern.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── 1. ALTER vertex_osm_ingest_run ────────────────────────────────────
  // RW does not honor "ADD COLUMN IF NOT EXISTS"; check first.
  const existingCols = await sql<{ column_name: string }>`
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'vertex_osm_ingest_run'
  `.execute(db);
  const have = new Set(existingCols.rows.map((r: any) => r.column_name));
  const addCol = async (name: string, type: string) => {
    if (!have.has(name)) {
      await sql.raw(`ALTER TABLE vertex_osm_ingest_run ADD COLUMN ${name} ${type}`).execute(db);
    }
  };
  await addCol('bench_variant', 'VARCHAR');
  await addCol('batch_size', 'BIGINT');
  await addCol('barrier_interval_ms', 'BIGINT');
  await addCol('checkpoint_frequency', 'BIGINT');
  await addCol('distributed_dml_enabled', 'BOOLEAN');
  await addCol('compute_cpu_request_m', 'BIGINT');
  await addCol('compute_memory_request_gi', 'BIGINT');
  await addCol('node_phase_seconds', 'DOUBLE PRECISION');
  await addCol('way_phase_seconds', 'DOUBLE PRECISION');
  await addCol('rel_phase_seconds', 'DOUBLE PRECISION');
  await addCol('aggregate_rows_per_sec', 'DOUBLE PRECISION');
  await addCol('edges_written', 'BIGINT');

  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_run_bench_variant ON vertex_osm_ingest_run (bench_variant)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_run_aggregate_rps ON vertex_osm_ingest_run (aggregate_rows_per_sec)`.execute(db);

  // ── 2. NEW vertex_osm_ingest_finding ──────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_osm_ingest_finding (
      finding_id          VARCHAR PRIMARY KEY,
      kind                VARCHAR NOT NULL,
      slug                VARCHAR NOT NULL,
      title               VARCHAR NOT NULL,
      description         VARCHAR NOT NULL,
      evidence_run_ids    VARCHAR,
      recommended_config  VARCHAR,
      speedup_pct         DOUBLE PRECISION,
      pbf_size_class      VARCHAR,
      created_at          TIMESTAMPTZ NOT NULL,
      author              VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_finding_kind ON vertex_osm_ingest_finding (kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_finding_slug ON vertex_osm_ingest_finding (slug)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_ingest_finding_pbf_size_class ON vertex_osm_ingest_finding (pbf_size_class)`.execute(db);

  // ── 3. NEW edge_osm_run_versus ────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS edge_osm_run_versus (
      edge_id           VARCHAR PRIMARY KEY,
      baseline_run_id   VARCHAR NOT NULL,
      variant_run_id    VARCHAR NOT NULL,
      baseline_rps      DOUBLE PRECISION NOT NULL,
      variant_rps       DOUBLE PRECISION NOT NULL,
      speedup_ratio     DOUBLE PRECISION NOT NULL,
      speedup_pct       DOUBLE PRECISION NOT NULL,
      conclusion        VARCHAR NOT NULL,
      compared_at       TIMESTAMPTZ NOT NULL
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_run_versus_baseline ON edge_osm_run_versus (baseline_run_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_run_versus_variant ON edge_osm_run_versus (variant_run_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_osm_run_versus_speedup_pct ON edge_osm_run_versus (speedup_pct)`.execute(db);

  // ── 4. NEW MV mv_osm_ingest_top_runs ──────────────────────────────────
  // Narrow projection over completed runs, ordered by aggregate_rows_per_sec
  // DESC. No GROUP BY, no MAX(varchar). Safe streaming MV.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_osm_ingest_top_runs AS
    SELECT
      run_id,
      source_did,
      bench_variant,
      batch_size,
      barrier_interval_ms,
      checkpoint_frequency,
      distributed_dml_enabled,
      nodes_written,
      ways_written,
      rel_rows_written,
      edges_written,
      aggregate_rows_per_sec,
      rows_per_sec AS vertex_rows_per_sec,
      node_phase_seconds,
      way_phase_seconds,
      rel_phase_seconds,
      EXTRACT(EPOCH FROM (completed_at - started_at)) AS wallclock_seconds,
      started_at,
      completed_at
    FROM vertex_osm_ingest_run
    WHERE status = 'completed'
    ORDER BY aggregate_rows_per_sec DESC NULLS LAST
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_osm_ingest_top_runs`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_osm_run_versus`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_osm_ingest_finding`.execute(db);

  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN edges_written`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN aggregate_rows_per_sec`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN rel_phase_seconds`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN way_phase_seconds`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN node_phase_seconds`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN compute_memory_request_gi`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN compute_cpu_request_m`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN distributed_dml_enabled`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN checkpoint_frequency`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN barrier_interval_ms`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN batch_size`.execute(db);
  await sql`ALTER TABLE vertex_osm_ingest_run DROP COLUMN bench_variant`.execute(db);
}
