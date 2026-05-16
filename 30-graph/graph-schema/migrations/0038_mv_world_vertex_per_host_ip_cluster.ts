import { Kysely, sql } from 'kysely';

/**
 * Migration 0038: Extend mv_world_vertex_per_host UNION to include IP cluster
 * vertex tables (vertex_patent / vertex_trademark / vertex_work) so
 * mv_world_coverage_live reflects real IP cluster ingest (currently stuck at 0%).
 *
 * DROP CASCADE both mv_world_coverage_live and mv_world_vertex_per_host,
 * then re-CREATE with extended UNION. Cluster is on 24Gi compute (post-0026 OOM),
 * all 3 new vertex tables are <10K rows, backfill trivial.
 *
 * Pre-flight:
 *   SELECT count(*) FROM vertex_patent;     -- should be 1-1000
 *   SELECT count(*) FROM vertex_trademark;  -- should be 1-1000
 *   SELECT count(*) FROM vertex_work;       -- should be 100-10000
 *
 * app_host mapping:
 *   vertex_patent    → 'patent'    (dim_world_domain: patent, world_total=200M)
 *   vertex_trademark → 'chizai'    (dim_world_domain: shohyo, world_total=70M)
 *   vertex_work      → 'chizai'    (dim_world_domain: chosakuken, world_total=100M)
 *
 * Note: trademark/copyright aliased to chizai via dim_app_host_alias (0037 companion).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      SELECT 'legal-entity' AS app_host, COUNT(*) AS cnt FROM vertex_legal_entity
      UNION ALL SELECT 'maps',         COUNT(*) FROM vertex_spatial
      UNION ALL SELECT 'gov',          COUNT(*) FROM vertex_gov_org
      UNION ALL SELECT 'dns',          COUNT(*) FROM vertex_dns_observation
      UNION ALL SELECT 'railway',      COUNT(*) FROM vertex_transport
      UNION ALL SELECT 'blockchain',   COUNT(*) FROM vertex_blockchain_actor
      UNION ALL SELECT 'gtin',         COUNT(*) FROM vertex_gtin_product
      UNION ALL SELECT 'media-gamers', COUNT(*) FROM vertex_game_actor
      UNION ALL SELECT 'media-gamers', COUNT(*) FROM vertex_game_item
      UNION ALL SELECT 'bank',         COUNT(*) FROM vertex_finance
      UNION ALL SELECT 'patent',       COUNT(*) FROM vertex_patent
      UNION ALL SELECT 'chizai',       COUNT(*) FROM vertex_trademark
      UNION ALL SELECT 'chizai',       COUNT(*) FROM vertex_work
    ) sub
    GROUP BY app_host`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_coverage_live AS
    SELECT
      d.domain, d.app_host, d.world_total, d.unit, d.sector,
      COALESCE(p.did_count, 0)    AS did_count,
      COALESCE(r.record_count, 0) AS record_count,
      COALESCE(v.vertex_count, 0) AS vertex_count,
      GREATEST(
        COALESCE(p.did_count, 0),
        COALESCE(r.record_count, 0),
        COALESCE(v.vertex_count, 0)
      ) AS collected,
      GREATEST(
        COALESCE(p.did_count, 0),
        COALESCE(r.record_count, 0),
        COALESCE(v.vertex_count, 0)
      )::double precision / NULLIF(d.world_total, 0) AS coverage_rate
    FROM dim_world_domain d
    LEFT JOIN mv_world_did_per_host    p ON p.app_host = d.app_host
    LEFT JOIN mv_world_record_per_host r ON r.app_host = d.app_host
    LEFT JOIN mv_world_vertex_per_host v ON v.app_host = d.app_host`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Re-apply 0025 original definition (exclude IP cluster tables)
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      SELECT 'legal-entity' AS app_host, COUNT(*) AS cnt FROM vertex_legal_entity
      UNION ALL SELECT 'maps',         COUNT(*) FROM vertex_spatial
      UNION ALL SELECT 'gov',          COUNT(*) FROM vertex_gov_org
      UNION ALL SELECT 'dns',          COUNT(*) FROM vertex_dns_observation
      UNION ALL SELECT 'railway',      COUNT(*) FROM vertex_transport
      UNION ALL SELECT 'blockchain',   COUNT(*) FROM vertex_blockchain_actor
      UNION ALL SELECT 'gtin',         COUNT(*) FROM vertex_gtin_product
      UNION ALL SELECT 'media-gamers', COUNT(*) FROM vertex_game_actor
      UNION ALL SELECT 'media-gamers', COUNT(*) FROM vertex_game_item
      UNION ALL SELECT 'bank',         COUNT(*) FROM vertex_finance
    ) sub
    GROUP BY app_host`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_coverage_live AS
    SELECT d.domain, d.app_host, d.world_total, d.unit, d.sector,
      COALESCE(p.did_count, 0) AS did_count,
      COALESCE(r.record_count, 0) AS record_count,
      COALESCE(v.vertex_count, 0) AS vertex_count,
      GREATEST(COALESCE(p.did_count,0), COALESCE(r.record_count,0), COALESCE(v.vertex_count,0)) AS collected,
      GREATEST(COALESCE(p.did_count,0), COALESCE(r.record_count,0), COALESCE(v.vertex_count,0))::double precision / NULLIF(d.world_total, 0) AS coverage_rate
    FROM dim_world_domain d
    LEFT JOIN mv_world_did_per_host    p ON p.app_host = d.app_host
    LEFT JOIN mv_world_record_per_host r ON r.app_host = d.app_host
    LEFT JOIN mv_world_vertex_per_host v ON v.app_host = d.app_host`.execute(db);
}
