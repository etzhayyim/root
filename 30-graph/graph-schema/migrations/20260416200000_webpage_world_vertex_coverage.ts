import { Kysely, sql } from 'kysely';

/**
 * Migration 20260416200000: Webpage world vertex coverage
 *
 * Problem: vertex_page (985M+ rows, common crawl ingest) is not tracked in
 * mv_world_vertex_per_host, leaving the 'webpage' domain stuck at 0.00%
 * (107 records / 50,000,000,000 world_total).
 *
 * Fix: Rebuild mv_world_vertex_per_host to include vertex_page under 'webpage'
 * app_host. This exposes ~985M crawled pages to coverage metrics.
 *
 * Expected post-migration coverage:
 *   webpage: 985M / 50B = ~1.97%
 *
 * WARNING: The rebuild triggers a full scan of all vertex tables including
 * vertex_page (985M rows). Apply only when cluster is idle and use
 * SET background_ddl = true before applying.
 *
 * Pre-flight: ensure mv_site_page_total has completed its backfill first
 * (SHOW JOBS returns 0 rows). This confirms vertex_page scan is stable.
 *
 * Apply: out-of-band via psql (kysely migrator blocked by ghost 20260415140000).
 * After apply: INSERT INTO kysely_migration (name, timestamp) VALUES
 *   ('20260416200000_webpage_world_vertex_coverage', now());
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // Must drop mv_world_coverage_live first (depends on mv_world_vertex_per_host)
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      SELECT 'legal-entity'  AS app_host, COUNT(*) AS cnt FROM vertex_legal_entity
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
      -- hospitality (from 20260416180000)
      UNION ALL SELECT 'hospitality',  COUNT(*) FROM vertex_accommodation
      -- talent / employment (from 20260416180000)
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_talent_cohort
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_skill
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_occupation
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_job_posting
      -- new: web page coverage
      UNION ALL SELECT 'webpage',      COUNT(*) FROM vertex_page
    ) sub
    GROUP BY app_host`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_coverage_live AS
    SELECT
      d.domain,
      d.app_host,
      d.world_total,
      d.unit,
      d.sector,
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
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);

  // Restore without vertex_page
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      SELECT 'legal-entity'  AS app_host, COUNT(*) AS cnt FROM vertex_legal_entity
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
      UNION ALL SELECT 'hospitality',  COUNT(*) FROM vertex_accommodation
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_talent_cohort
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_skill
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_occupation
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_job_posting
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
