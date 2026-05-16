import type { Kysely } from "kysely";
import { sql } from "kysely";

async function baseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_id VARCHAR,
      owner_did VARCHAR,
      label VARCHAR,
      status VARCHAR,
      stream_id VARCHAR,
      agent_did VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_record_id`)} ON ${sql.table(table)} (record_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_stream`)} ON ${sql.table(table)} (stream_id, created_at)`.execute(db);
}

async function baseEdge(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  // compintel — Competitive Intelligence Dashboard (ADR-2605072000)
  // No PII — all data is public competitive intelligence (sensitivity_ord=0)

  // Competitor tracking records
  await baseVertex(db, "vertex_compintel_competitor");
  await sql`ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS competitor_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS competitor_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS website VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS industry VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS tracking_dimensions TEXT`.execute(db);
  await sql`ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS threat_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_compintel_competitor ADD COLUMN IF NOT EXISTS last_refreshed_at VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_compintel_competitor_id ON vertex_compintel_competitor (competitor_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_compintel_competitor_industry ON vertex_compintel_competitor (industry)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_compintel_competitor_threat ON vertex_compintel_competitor (threat_score)`.execute(db);

  // Intelligence snapshots (one per refresh cycle per competitor)
  await baseVertex(db, "vertex_compintel_snapshot");
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS snapshot_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS competitor_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS latest_summary TEXT`.execute(db);
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS pricing_signals TEXT`.execute(db);
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS product_signals TEXT`.execute(db);
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS hiring_signals TEXT`.execute(db);
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS funding_signals TEXT`.execute(db);
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS press_signals TEXT`.execute(db);
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS threat_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_compintel_snapshot ADD COLUMN IF NOT EXISTS content_hash VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_compintel_snapshot_competitor ON vertex_compintel_snapshot (competitor_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_compintel_snapshot_created ON vertex_compintel_snapshot (competitor_id, created_at)`.execute(db);

  // Alerts for significant changes detected
  await baseVertex(db, "vertex_compintel_alert");
  await sql`ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS alert_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS competitor_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS dimension VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS summary TEXT`.execute(db);
  await sql`ALTER TABLE vertex_compintel_alert ADD COLUMN IF NOT EXISTS severity VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_compintel_alert_competitor ON vertex_compintel_alert (competitor_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_compintel_alert_severity ON vertex_compintel_alert (severity)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_compintel_alert_created ON vertex_compintel_alert (created_at)`.execute(db);

  // Competitor → snapshot edge
  await baseEdge(db, "edge_compintel_snapshot");
  await sql`ALTER TABLE edge_compintel_snapshot ADD COLUMN IF NOT EXISTS competitor_id VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_compintel_snapshot ADD COLUMN IF NOT EXISTS snapshot_id VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_compintel_snapshot_competitor ON edge_compintel_snapshot (competitor_id)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_compintel_snapshot`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_compintel_alert`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_compintel_snapshot`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_compintel_competitor`.execute(db);
}
