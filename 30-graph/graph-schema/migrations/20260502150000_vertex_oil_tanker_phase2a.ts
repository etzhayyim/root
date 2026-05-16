import { Kysely, sql } from "kysely";

/**
 * Phase 2A — oil_tanker domain.
 *
 * Adds vertex_oil_tanker (IMO/MMSI/vessel_class/flag/DWT/operator_did/sanctions)
 * + oil_tanker world_total=10,000 entry in dim_world_domain.
 * Rebuilds mv_world_vertex_per_host and mv_world_coverage_live to include it.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oil_tanker (
      vertex_id          VARCHAR PRIMARY KEY,
      imo                VARCHAR,
      mmsi               VARCHAR,
      vessel_name        VARCHAR,
      vessel_class       VARCHAR,
      flag_country       VARCHAR,
      dwt                BIGINT,
      operator_did       VARCHAR,
      built_year         BIGINT,
      sanctions_status   VARCHAR,
      status             VARCHAR,
      collection         VARCHAR,
      actor_did          VARCHAR,
      org_did            VARCHAR,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      created_at         VARCHAR
    )
  `.execute(db);

  // Add oil_tanker domain to dim_world_domain (RW has no ON CONFLICT: SELECT-then-INSERT)
  const existing = await sql`
    SELECT 1 FROM dim_world_domain WHERE domain = 'oil_tanker' LIMIT 1
  `.execute(db);
  if ((existing.rows as unknown[]).length === 0) {
    await sql`
      INSERT INTO dim_world_domain
        (domain, app_host, world_total, unit, sector)
      VALUES
        ('oil_tanker', 'oil-coverage', 10000,
         'oil tankers (VLCC/Suezmax/Aframax/MR/LR/VLGC)', 'maritime-energy')
    `.execute(db);
  }

  // Rebuild mv_world_vertex_per_host adding vertex_oil_tanker
  await sql`DROP VIEW IF EXISTS view_world_coverage_live`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_world_vertex_per_host AS
    SELECT app_host, SUM(cnt) AS vertex_count FROM (
      SELECT 'maps'                AS app_host, COUNT(*) AS cnt FROM vertex_spatial
      UNION ALL SELECT 'maps',                  COUNT(*)          FROM vertex_transport
      UNION ALL SELECT 'gov',                   COUNT(*)          FROM vertex_gov_org
      UNION ALL SELECT 'gov',                   COUNT(*)          FROM vertex_gov_municipality
      UNION ALL SELECT 'dns',                   COUNT(*)          FROM vertex_dns_observation
      UNION ALL SELECT 'dns',                   COUNT(*)          FROM vertex_domain
      UNION ALL SELECT 'blockchain',            COUNT(*)          FROM vertex_blockchain_actor
      UNION ALL SELECT 'gtin',                  COUNT(*)          FROM vertex_gtin_product
      UNION ALL SELECT 'media-gamers',          COUNT(*)          FROM vertex_game_actor
      UNION ALL SELECT 'media-gamers',          COUNT(*)          FROM vertex_game_item
      UNION ALL SELECT 'media-gamers',          COUNT(*)          FROM vertex_game_title
      UNION ALL SELECT 'bank',                  COUNT(*)          FROM vertex_finance
      UNION ALL SELECT 'patent',                COUNT(*)          FROM vertex_patent
      UNION ALL SELECT 'chizai',                COUNT(*)          FROM vertex_trademark
      UNION ALL SELECT 'chizai',                COUNT(*)          FROM vertex_work
      UNION ALL SELECT 'hospitality',           COUNT(*)          FROM vertex_accommodation
      UNION ALL SELECT 'talent',                COUNT(*)          FROM vertex_talent_cohort
      UNION ALL SELECT 'talent',                COUNT(*)          FROM vertex_skill
      UNION ALL SELECT 'talent',                COUNT(*)          FROM vertex_occupation
      UNION ALL SELECT 'talent',                COUNT(*)          FROM vertex_occupation_wikidata
      UNION ALL SELECT 'talent',                COUNT(*)          FROM vertex_occupation_bls
      UNION ALL SELECT 'talent',                COUNT(*)          FROM vertex_job_posting
      UNION ALL SELECT 'sanctions',             COUNT(*)          FROM vertex_open_ofac_sanctions_sdn
      UNION ALL SELECT 'crypto-asset-freeze',   COUNT(*)          FROM vertex_crypto_asset_freeze_incident
      UNION ALL SELECT 'bengoshi',              COUNT(*)          FROM vertex_adr_case
      UNION ALL SELECT 'bengoshi',              COUNT(*)          FROM vertex_adr_arbitrator
      UNION ALL SELECT 'bengoshi',              COUNT(*)          FROM vertex_lawyer
      UNION ALL SELECT 'npo',                   COUNT(*)          FROM vertex_legal_aid_case
      UNION ALL SELECT 'npo',                   COUNT(*)          FROM vertex_legal_aid_office
      UNION ALL SELECT 'natural-person',        COUNT(*)          FROM vertex_natural_person
      UNION ALL SELECT 'ipaddress',             COUNT(*)          FROM vertex_ip_address
      UNION ALL SELECT 'keiyaku',               COUNT(*)          FROM vertex_keiyaku_contract_canonical
      UNION ALL SELECT 'keiyaku',               COUNT(*)          FROM vertex_keiyaku_contract_observation
      UNION ALL SELECT 'kyber',                 COUNT(*)          FROM vertex_office_document
      UNION ALL SELECT 'judge',                 COUNT(*)          FROM vertex_judge
      UNION ALL SELECT 'public-fund',           COUNT(*)          FROM vertex_fund WHERE fund_kind IN ('government', 'sovereign')
      UNION ALL SELECT 'securities',            COUNT(*)          FROM vertex_fund WHERE fund_kind IN ('investor', 'mutual', 'pension', 'private')
      UNION ALL SELECT 'mine',                  COUNT(*)          FROM vertex_rare_earth_coverage
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_oil_company
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_oil_field
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_oil_basin
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_oil_pipeline
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_oil_terminal
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_crude_grade
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_pricing_benchmark
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_oil_trade
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_oil_cargo
      UNION ALL SELECT 'oil-coverage',          COUNT(*)          FROM vertex_oil_tanker
      UNION ALL SELECT 'webpage',               cnt               FROM mv_vertex_page_count
    ) AS sub
    GROUP BY app_host
  `.execute(db);

  await sql`GRANT SELECT ON MATERIALIZED VIEW mv_world_vertex_per_host TO root`.execute(db);
  await sql`GRANT SELECT ON MATERIALIZED VIEW mv_world_vertex_per_host TO kaisya_app`.execute(db);

  await sql`
    CREATE VIEW mv_world_coverage_live AS
    WITH gov_override AS (
      SELECT CAST('gov' AS CHARACTER VARYING) AS domain,
             government_org_count AS record_count,
             CAST(0 AS BIGINT) AS vertex_count
      FROM mv_gov_coverage_dedup
      UNION ALL
      SELECT CAST('gov_admin_area' AS CHARACTER VARYING),
             admin_area_count,
             CAST(0 AS BIGINT)
      FROM mv_gov_coverage_dedup
    ),
    domain_counts AS (
      SELECT d.domain, d.app_host, d.world_total, d.unit, d.sector,
        CAST(COALESCE(p.did_count, 0) AS BIGINT) AS did_count,
        CASE WHEN go.domain IS NOT NULL THEN go.record_count
             ELSE CAST(COALESCE(r.record_count, 0) AS BIGINT) END AS record_count,
        CAST(COALESCE(v.vertex_count, 0) AS BIGINT) AS vertex_count
      FROM dim_world_domain AS d
      LEFT JOIN mv_world_did_per_host    AS p  ON p.app_host = d.app_host
      LEFT JOIN mv_world_record_per_host AS r  ON r.app_host = d.app_host
      LEFT JOIN gov_override             AS go ON go.domain  = d.domain
      LEFT JOIN mv_world_vertex_per_host AS v  ON v.app_host = d.app_host
    )
    SELECT domain, app_host, world_total, unit, sector,
      did_count, record_count, vertex_count,
      GREATEST(did_count, record_count, vertex_count) AS collected,
      CASE WHEN world_total > 0
           THEN CAST(GREATEST(did_count, record_count, vertex_count) AS DOUBLE) / CAST(world_total AS DOUBLE)
           ELSE 0.0 END AS coverage_rate,
      CASE WHEN world_total > 0
           THEN 1.0 - CAST(GREATEST(did_count, record_count, vertex_count) AS DOUBLE) / CAST(world_total AS DOUBLE)
           ELSE 1.0 END AS gap_rate,
      CAST(GREATEST(world_total - GREATEST(did_count, record_count, vertex_count), 0) AS BIGINT) AS remaining
    FROM domain_counts
  `.execute(db);

  await sql`
    CREATE VIEW view_world_coverage_live AS SELECT * FROM mv_world_coverage_live
  `.execute(db);

  await sql`GRANT SELECT ON mv_world_coverage_live TO root`.execute(db);
  await sql`GRANT SELECT ON view_world_coverage_live TO root`.execute(db);
  await sql`GRANT SELECT ON mv_world_coverage_live TO kaisya_app`.execute(db);
  await sql`GRANT SELECT ON view_world_coverage_live TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_world_coverage_live`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_vertex_per_host`.execute(db);
  await sql`DELETE FROM dim_world_domain WHERE domain = 'oil_tanker'`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oil_tanker`.execute(db);
}
