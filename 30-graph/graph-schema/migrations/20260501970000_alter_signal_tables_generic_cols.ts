import type { Kysely } from "kysely";
import { sql } from "kysely";

// Fix schema mismatch: aria_signal.py inserts (signal_axis, source,
// sample_count, metadata_json, created_at) but the tables were created
// without those generic columns. Also recreate mv_signal_entropy to use
// `signal_axis` alias matching the Python query.

export async function up(db: Kysely<unknown>): Promise<void> {
  // Drop dependent MVs first (in reverse dependency order)
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_signal_area_integral`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_signal_entropy`.execute(db);

  // Add generic signal columns to all 6 signal tables.
  // RisingWave does not support multi-column ADD COLUMN in one statement —
  // each column must be a separate ALTER TABLE.
  const TABLES = [
    "vertex_signal_attention",
    "vertex_signal_request",
    "vertex_signal_money",
    "vertex_signal_emotion",
    "vertex_signal_market",
    "vertex_signal_influence",
  ] as const;
  const COLS: [string, string][] = [
    ["signal_axis",   "VARCHAR"],
    ["source",        "VARCHAR"],
    ["sample_count",  "BIGINT DEFAULT 0"],
    ["metadata_json", "VARCHAR"],
    ["created_at",    "TIMESTAMPTZ"],
  ];
  for (const tbl of TABLES) {
    for (const [col, type] of COLS) {
      await sql.raw(`ALTER TABLE ${tbl} ADD COLUMN IF NOT EXISTS ${col} ${type}`).execute(db);
    }
  }

  // Recreate mv_signal_entropy with signal_axis column name
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_signal_entropy AS
    SELECT
      signal_axis,
      tick,
      AVG(entropy_h)           AS h_avg,
      MAX(h_max)               AS h_max,
      AVG(eta)                 AS eta,
      SUM(axis_weight * eta)   AS area_contrib
    FROM (
      SELECT 'attention' AS signal_axis,
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)) AS tick,
             entropy_h, COALESCE(h_max, 10.0) AS h_max, eta, COALESCE(axis_weight, 1.45) AS axis_weight
        FROM vertex_signal_attention
      UNION ALL
      SELECT 'request',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 9.0), eta, COALESCE(axis_weight, 1.35)
        FROM vertex_signal_request
      UNION ALL
      SELECT 'money',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 6.6), eta, COALESCE(axis_weight, 1.45)
        FROM vertex_signal_money
      UNION ALL
      SELECT 'emotion',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 6.0), eta, COALESCE(axis_weight, 1.55)
        FROM vertex_signal_emotion
      UNION ALL
      SELECT 'market',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 7.6), eta, COALESCE(axis_weight, 1.35)
        FROM vertex_signal_market
      UNION ALL
      SELECT 'influence',
             DATE_TRUNC('minute', COALESCE(created_at, captured_at)),
             entropy_h, COALESCE(h_max, 6.6), eta, COALESCE(axis_weight, 1.80)
        FROM vertex_signal_influence
    ) t
    GROUP BY signal_axis, tick
  `.execute(db);

  // Recreate downstream MV
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_signal_area_integral AS
    SELECT
      tick,
      SUM(area_contrib)         AS a_info,
      SUM(area_contrib) / 4.475 AS eta_global,
      CASE
        WHEN SUM(area_contrib) < 1.567 THEN 'BELOW_BASELINE'
        WHEN SUM(area_contrib) < 3.0   THEN 'PARTIAL'
        ELSE 'OPTIMAL'
      END                       AS coverage_grade
    FROM mv_signal_entropy
    GROUP BY tick
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_signal_area_integral`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_signal_entropy`.execute(db);
  // Note: columns added by IF NOT EXISTS cannot be cleanly removed without
  // knowing the prior state. Leave tables with extra columns on rollback.
}
