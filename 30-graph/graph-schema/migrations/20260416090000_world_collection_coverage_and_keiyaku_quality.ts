import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * 2026-04-16
 * - keiyaku canonicalization graph tables (vertex/edge)
 * - world coverage by (domain, collection)
 * - daily quality snapshot table + latest MV
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // -- A) keiyaku dedupe graph ------------------------------------------------
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_keiyaku_contract_canonical (
      vertex_id         VARCHAR PRIMARY KEY,
      contract_id       VARCHAR NOT NULL,
      canonical_rkey    VARCHAR NOT NULL,
      canonical_uri     VARCHAR NOT NULL,
      latest_start_date VARCHAR,
      latest_end_date   VARCHAR,
      max_award_amount  DOUBLE PRECISION,
      awarding_agency   VARCHAR,
      recipient_name    VARCHAR,
      variant_count     BIGINT NOT NULL DEFAULT 0,
      updated_at        VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_keiyaku_contract_observation (
      vertex_id       VARCHAR PRIMARY KEY,
      uri             VARCHAR NOT NULL,
      rkey            VARCHAR NOT NULL,
      contract_id     VARCHAR,
      start_date      VARCHAR,
      end_date        VARCHAR,
      award_amount    DOUBLE PRECISION,
      awarding_agency VARCHAR,
      recipient_name  VARCHAR,
      observed_at     VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_keiyaku_canonicalizes (
      edge_id     VARCHAR PRIMARY KEY,
      src_vid     VARCHAR NOT NULL,
      dst_vid     VARCHAR NOT NULL,
      relation    VARCHAR NOT NULL,
      created_at  VARCHAR NOT NULL
    )
  `.execute(db);

  // -- B) world coverage by collection ----------------------------------------
  await sql`
    CREATE TABLE IF NOT EXISTS dim_world_domain_collection (
      domain      VARCHAR NOT NULL,
      app_host    VARCHAR NOT NULL,
      collection  VARCHAR NOT NULL,
      world_total BIGINT NOT NULL,
      unit        VARCHAR NOT NULL DEFAULT '',
      sector      VARCHAR NOT NULL DEFAULT '',
      PRIMARY KEY (domain, collection)
    )
  `.execute(db);

  await sql`DELETE FROM dim_world_domain_collection`.execute(db);

  await sql`
    INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    SELECT
      d.domain,
      d.app_host,
      CASE
        WHEN d.app_host = 'ndc' THEN 'com.etzhayyim.apps.fda.ndc'
        WHEN d.app_host = 'keiyaku' THEN 'com.etzhayyim.apps.keiyaku.contract'
        WHEN d.app_host = 'seizo' THEN 'com.etzhayyim.apps.seizo.factory_site'
        WHEN d.app_host = 'serial' THEN 'com.etzhayyim.apps.serial.mac_prefix'
        WHEN d.app_host = 'malak' THEN 'com.etzhayyim.apps.malak.cve'
        WHEN d.app_host = 'shigotoba' THEN 'com.etzhayyim.apps.shigotoba.shigotoba'
        ELSE 'com.etzhayyim.coverage.bootstrap'
      END AS collection,
      d.world_total,
      d.unit,
      d.sector
    FROM dim_world_domain d
  `.execute(db);

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
    )
    SELECT
      app_host,
      collection,
      COUNT(*)::BIGINT AS record_count
    FROM normalized
    GROUP BY app_host, collection
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_collection_coverage_live`.execute(db);
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

  // -- C) quality snapshots ----------------------------------------------------
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_data_quality_daily (
      snapshot_date                VARCHAR NOT NULL,
      repo                         VARCHAR NOT NULL,
      collection                   VARCHAR NOT NULL,
      total_count                  BIGINT NOT NULL,
      bad_json_count               BIGINT NOT NULL,
      duplicate_rkey_count         BIGINT NOT NULL,
      missing_core_count           BIGINT NOT NULL,
      invalid_geo_count            BIGINT NOT NULL,
      duplicate_business_key_count BIGINT NOT NULL,
      note                         VARCHAR,
      created_at                   VARCHAR NOT NULL,
      PRIMARY KEY (snapshot_date, repo, collection)
    )
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_data_quality_latest`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_data_quality_latest AS
    WITH last_day AS (
      SELECT repo, collection, MAX(snapshot_date) AS snapshot_date
      FROM vertex_data_quality_daily
      GROUP BY repo, collection
    )
    SELECT d.*
    FROM vertex_data_quality_daily d
    JOIN last_day l
      ON d.repo = l.repo
     AND d.collection = l.collection
     AND d.snapshot_date = l.snapshot_date
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_data_quality_latest`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_data_quality_daily`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_collection_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_record_per_host_collection`.execute(db);
  await sql`DROP TABLE IF EXISTS dim_world_domain_collection`.execute(db);

  await sql`DROP TABLE IF EXISTS edge_keiyaku_canonicalizes`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_keiyaku_contract_observation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_keiyaku_contract_canonical`.execute(db);
}
