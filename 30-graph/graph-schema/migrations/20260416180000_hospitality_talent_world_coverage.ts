import { Kysely, sql } from "kysely";

/**
 * Migration 20260416180000: Hospitality + Talent world coverage
 *
 * Problem: vertex_accommodation (828K rows) and talent/occupation tables
 * (vertex_talent_cohort 21K, vertex_skill 14K, vertex_occupation 5K,
 *  vertex_job_posting 7K) exist but are NOT tracked in mv_world_coverage_live.
 * This renders 876K+ rows invisible to domain coverage metrics.
 *
 * Fix:
 *   1. INSERT new dim_world_domain rows for hospitality + talent app hosts.
 *   2. DROP CASCADE mv_world_coverage_live → mv_world_vertex_per_host.
 *   3. RECREATE mv_world_vertex_per_host with vertex_accommodation + talent tables.
 *   4. RECREATE mv_world_coverage_live (unchanged SELECT, new vertex data flows in).
 *
 * Pre-flight counts (2026-04-16):
 *   vertex_accommodation   = 828,241  (hospitality OSM ingest, 240 countries)
 *   vertex_talent_cohort   =  21,373  (ILOSTAT workforce cohorts)
 *   vertex_skill           =  13,896  (ESCO skills)
 *   vertex_occupation      =   5,172  (ISCO-08 + O*NET)
 *   vertex_job_posting     =   7,074  (public job postings)
 *
 * Expected post-migration coverage:
 *   accommodation    828K / 1,500K = ~55%
 *   hotel            828K /   700K = ~118% (over 100% — includes all lodging)
 *   occupation_code  5,172 / 5,172 = 100%
 *   skill_taxonomy  13,896 / 50,000 = ~28%
 *
 * MV safety:
 *   vertex_accommodation: 828K rows — streaming actor count increases.
 *   Set background_ddl = true before applying to avoid blocking.
 *   Max(varchar) not used; only COUNT(*) → agg state = cardinality-safe.
 *
 * Apply: out-of-band via psql (kysely migrator blocked by ghost 20260415140000).
 * After apply: INSERT INTO kysely_migration (name, timestamp) VALUES
 *   ('20260416180000_hospitality_talent_world_coverage', now());
 */

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── 1. Add new dim_world_domain entries ──────────────────────────────
  await sql`DELETE FROM dim_world_domain
    WHERE domain IN (
      'accommodation', 'hotel', 'minpaku', 'ryokan',
      'occupation_code', 'skill_taxonomy', 'job_posting', 'talent_cohort_stat'
    )`.execute(db);

  await sql`INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector) VALUES
    -- Hospitality: all lodging (hotels + hostels + B&B + camping etc.)
    ('accommodation',       'hospitality', 1500000, 'accommodation properties', 'hospitality'),
    -- Hotels only subset (world_total < accommodation since hotels are a subset)
    ('hotel',               'hospitality',  700000, 'hotels (star-rated)',      'hospitality'),
    -- Japan-specific: minpaku (民泊) + ryokan
    ('minpaku',             'hospitality',   60000, 'minpaku / home-stay JP',   'hospitality'),
    ('ryokan',              'hospitality',    3000, 'ryokan JP',                'hospitality'),
    -- Talent / Employment
    ('occupation_code',     'talent',         5172, 'ISCO/O*NET occupation codes', 'employment'),
    ('skill_taxonomy',      'talent',        50000, 'ESCO + O*NET skill nodes',    'employment'),
    ('job_posting',         'talent',    300000000, 'active job postings globally','employment'),
    ('talent_cohort_stat',  'talent',    600000000, 'ILOSTAT workforce cohorts',   'employment')
  `.execute(db);

  // ── 2. Rebuild mv_world_vertex_per_host with new tables ──────────────
  // DROP CASCADE automatically drops mv_world_coverage_live first
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      -- existing entries (from 0025 + 0038)
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
      -- new: hospitality
      UNION ALL SELECT 'hospitality',  COUNT(*) FROM vertex_accommodation
      -- new: talent / employment
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_talent_cohort
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_skill
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_occupation
      UNION ALL SELECT 'talent',       COUNT(*) FROM vertex_job_posting
    ) sub
    GROUP BY app_host`.execute(db);

  // ── 3. Recreate mv_world_coverage_live (SELECT unchanged) ────────────
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
  // Remove new dim_world_domain entries
  await sql`DELETE FROM dim_world_domain
    WHERE domain IN (
      'accommodation', 'hotel', 'minpaku', 'ryokan',
      'occupation_code', 'skill_taxonomy', 'job_posting', 'talent_cohort_stat'
    )`.execute(db);

  // Restore mv_world_vertex_per_host without new tables
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
