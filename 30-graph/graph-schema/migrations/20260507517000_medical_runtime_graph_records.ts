import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Medical runtime graph records.
 *
 * `vertex_repo_record` is reserved for social/AT feed records. Medical
 * canonical ingest rows are promoted to `vertex_medical` and counted from
 * there for world coverage.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS collection VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS source VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS source_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS ingested_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS created_at VARCHAR`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_medical_coverage_cursor (
      target_key VARCHAR PRIMARY KEY,
      cursor_value TEXT NOT NULL,
      records_ingested BIGINT,
      last_coverage_rate DOUBLE PRECISION,
      last_error TEXT,
      updated_at VARCHAR,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_medical_source_record (
      edge_id VARCHAR PRIMARY KEY,
      source_id VARCHAR NOT NULL,
      record_vid VARCHAR NOT NULL,
      collection VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_medical_collection ON vertex_medical (collection)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_medical_code ON vertex_medical (code)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_medical_category ON vertex_medical (category)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_medical_source ON vertex_medical (source)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_medical_cursor_updated ON vertex_medical_coverage_cursor (updated_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_medical_source_record_source ON edge_medical_source_record (source_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_medical_source_record_record ON edge_medical_source_record (record_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_medical_source_record_collection ON edge_medical_source_record (collection)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_medical_record_count_by_collection`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_medical_record_count_by_collection AS
    SELECT collection, category, count(*)::BIGINT AS record_count, max(ingested_at) AS latest_ingested_at
    FROM vertex_medical
    WHERE collection IS NOT NULL AND collection <> ''
    GROUP BY collection, category
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_medical_record_count_by_source`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_medical_record_count_by_source AS
    SELECT source_id, collection, count(*)::BIGINT AS record_count, max(updated_at) AS latest_linked_at
    FROM edge_medical_source_record
    GROUP BY source_id, collection
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_collection_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_record_per_host_collection`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_world_record_per_host_collection AS
    WITH normalized AS (
      SELECT
        COALESCE(a.canonical_host, split_part(split_part(r.repo, 'did:web:', 2), '.', 1)) AS app_host,
        r.collection AS collection
      FROM vertex_repo_record r
      LEFT JOIN dim_app_host_alias a
        ON split_part(split_part(r.repo, 'did:web:', 2), '.', 1) = a.alias_host
      UNION ALL
      SELECT 'iryo' AS app_host, m.collection AS collection
      FROM vertex_medical m
      WHERE m.collection IS NOT NULL AND m.collection <> ''
    )
    SELECT app_host, collection, COUNT(*)::BIGINT AS record_count
    FROM normalized
    GROUP BY app_host, collection
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_world_collection_coverage_live AS
    SELECT
      d.domain,
      d.app_host,
      d.collection,
      d.world_total,
      d.unit,
      d.sector,
      COALESCE(wd.did_count, 0)::BIGINT AS did_count,
      COALESCE(rc.record_count, 0)::BIGINT AS record_count,
      GREATEST(COALESCE(wd.did_count, 0), COALESCE(rc.record_count, 0))::BIGINT AS collected,
      CASE
        WHEN d.world_total > 0
        THEN (GREATEST(COALESCE(wd.did_count, 0), COALESCE(rc.record_count, 0))::DOUBLE PRECISION / d.world_total::DOUBLE PRECISION)
        ELSE 0.0
      END AS coverage_rate
    FROM dim_world_domain_collection d
    LEFT JOIN mv_world_did_per_host wd
      ON wd.app_host = d.app_host
    LEFT JOIN mv_world_record_per_host_collection rc
      ON rc.app_host = d.app_host AND rc.collection = d.collection
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_collection_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_record_per_host_collection`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_medical_record_count_by_source`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_medical_record_count_by_collection`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_medical_source_record`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_world_record_per_host_collection AS
    WITH normalized AS (
      SELECT
        COALESCE(a.canonical_host, split_part(split_part(r.repo, 'did:web:', 2), '.', 1)) AS app_host,
        r.collection AS collection
      FROM vertex_repo_record r
      LEFT JOIN dim_app_host_alias a
        ON split_part(split_part(r.repo, 'did:web:', 2), '.', 1) = a.alias_host
    )
    SELECT app_host, collection, COUNT(*)::BIGINT AS record_count
    FROM normalized
    GROUP BY app_host, collection
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_world_collection_coverage_live AS
    SELECT
      d.domain,
      d.app_host,
      d.collection,
      d.world_total,
      d.unit,
      d.sector,
      COALESCE(wd.did_count, 0)::BIGINT AS did_count,
      COALESCE(rc.record_count, 0)::BIGINT AS record_count,
      GREATEST(COALESCE(wd.did_count, 0), COALESCE(rc.record_count, 0))::BIGINT AS collected,
      CASE
        WHEN d.world_total > 0
        THEN (GREATEST(COALESCE(wd.did_count, 0), COALESCE(rc.record_count, 0))::DOUBLE PRECISION / d.world_total::DOUBLE PRECISION)
        ELSE 0.0
      END AS coverage_rate
    FROM dim_world_domain_collection d
    LEFT JOIN mv_world_did_per_host wd
      ON wd.app_host = d.app_host
    LEFT JOIN mv_world_record_per_host_collection rc
      ON rc.app_host = d.app_host AND rc.collection = d.collection
  `.execute(db);
}
