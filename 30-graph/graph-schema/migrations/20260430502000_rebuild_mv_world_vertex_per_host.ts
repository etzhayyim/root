import { Kysely, sql } from "kysely";

/**
 * Rebuild mv_world_vertex_per_host — the MV was dropped between sessions,
 * causing mv_world_coverage_live to show vertex_count=0 for all domains.
 *
 * Changes from the last live definition (20260416200000 + later rebuilds):
 * - Adds 'sanctions' app_host → vertex_open_ofac_sanctions_sdn (new 27-domain addition)
 * - Adds 'npo' app_host → vertex_legal_aid_office + vertex_legal_aid_case
 * - Adds 'bengoshi' app_host → vertex_adr_case + vertex_adr_arbitrator
 * - Excludes vertex_page (985M rows, webpage domain) to avoid B2 rate-limit storms;
 *   webpage coverage is adequately tracked via mv_world_record_per_host AT records.
 *
 * Apply out-of-band via psql with locality_backfill:
 *   ALTER SYSTEM SET barrier_interval_ms = 5000;
 *   ALTER SYSTEM SET checkpoint_frequency = 30;
 *   SET enable_locality_backfill = true;
 *   SET background_ddl = true;
 *   [DDL here]
 *   SET background_ddl = false;
 *
 * After apply, INSERT INTO kysely_migration manually.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // Drop dependents first
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      -- legal-entity: bulk-loaded, not in AT records (190M rows)
      SELECT 'legal-entity'  AS app_host, COUNT(*) AS cnt FROM vertex_legal_entity
      -- maps: spatial features (5M rows)
      UNION ALL SELECT 'maps',          COUNT(*) FROM vertex_spatial
      -- maps: transit (small)
      UNION ALL SELECT 'maps',          COUNT(*) FROM vertex_transport
      -- gov: org and municipality
      UNION ALL SELECT 'gov',           COUNT(*) FROM vertex_gov_org
      UNION ALL SELECT 'gov',           COUNT(*) FROM vertex_gov_municipality
      -- dns: passive DNS observations
      UNION ALL SELECT 'dns',           COUNT(*) FROM vertex_dns_observation
      -- blockchain: addresses
      UNION ALL SELECT 'blockchain',    COUNT(*) FROM vertex_blockchain_actor
      -- gtin: barcoded products
      UNION ALL SELECT 'gtin',          COUNT(*) FROM vertex_gtin_product
      -- media-gamers: game actors and items
      UNION ALL SELECT 'media-gamers',  COUNT(*) FROM vertex_game_actor
      UNION ALL SELECT 'media-gamers',  COUNT(*) FROM vertex_game_item
      -- finance
      UNION ALL SELECT 'bank',          COUNT(*) FROM vertex_finance
      -- ip / chizai
      UNION ALL SELECT 'patent',        COUNT(*) FROM vertex_patent
      UNION ALL SELECT 'chizai',        COUNT(*) FROM vertex_trademark
      UNION ALL SELECT 'chizai',        COUNT(*) FROM vertex_work
      -- hospitality
      UNION ALL SELECT 'hospitality',   COUNT(*) FROM vertex_accommodation
      -- talent / employment
      UNION ALL SELECT 'talent',        COUNT(*) FROM vertex_talent_cohort
      UNION ALL SELECT 'talent',        COUNT(*) FROM vertex_skill
      UNION ALL SELECT 'talent',        COUNT(*) FROM vertex_occupation
      UNION ALL SELECT 'talent',        COUNT(*) FROM vertex_job_posting
      -- sanctions (new: 27-domain additions)
      UNION ALL SELECT 'sanctions',     COUNT(*) FROM vertex_open_ofac_sanctions_sdn
      -- adr (new: intake table)
      UNION ALL SELECT 'bengoshi',      COUNT(*) FROM vertex_adr_case
      UNION ALL SELECT 'bengoshi',      COUNT(*) FROM vertex_adr_arbitrator
      -- legal-aid (new: intake table)
      UNION ALL SELECT 'npo',           COUNT(*) FROM vertex_legal_aid_case
      UNION ALL SELECT 'npo',           COUNT(*) FROM vertex_legal_aid_office
    ) sub
    GROUP BY app_host
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);
}
