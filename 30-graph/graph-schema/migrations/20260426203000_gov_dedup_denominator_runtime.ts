import { Kysely, sql } from "kysely";

/**
 * Gov coverage repair: split government organizations from administrative
 * areas, count deduped entity keys, and expose per-org BPMN/MCP runtime refs.
 *
 * The previous `gov` coverage mixed `ai.gftd.apps.gov.entity` city/village/
 * settlement records into the "government agencies" denominator, which pushed
 * gov coverage above 100%. This migration keeps `gov` for organizations and
 * moves territorial/settlement entities to `gov_admin_area`.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE dim_world_domain
       SET app_host = 'gov',
           world_total = 500000,
           unit = 'government agencies / ministries / public bodies (global)',
           sector = 'governance'
     WHERE domain = 'gov'
  `.execute(db);

  await sql`
    DELETE FROM dim_world_domain
     WHERE domain = 'gov_admin_area'
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain (domain, app_host, world_total, unit, sector)
    VALUES (
      'gov_admin_area',
      'gov',
      500000,
      'administrative areas / municipalities / settlements in gov registry target',
      'governance'
    )
  `.execute(db);

  await sql`
    DELETE FROM dim_world_domain_collection
     WHERE domain IN ('gov', 'gov_admin_area')
        OR collection IN (
          'ai.gftd.apps.gov.entity',
          'ai.gftd.apps.gov.agency',
          'ai.gftd.apps.gov.ministry',
          'govOrg',
          'govOrgSiteDep',
          'governanceContract'
        )
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES
      ('gov', 'gov', 'ai.gftd.apps.gov.agency', 500000, 'government agencies / public bodies', 'governance'),
      ('gov', 'gov', 'ai.gftd.apps.gov.ministry', 500000, 'ministries', 'governance'),
      ('gov', 'gov', 'govOrg', 500000, 'government organizations', 'governance'),
      ('gov', 'gov', 'governanceContract', 500000, 'government organization governance contracts', 'governance'),
      ('gov_admin_area', 'gov', 'ai.gftd.apps.gov.entity', 500000, 'administrative areas / municipalities / settlements', 'governance'),
      ('gov_admin_area', 'gov', 'govOrgSiteDep', 500000, 'government organization site dependencies / area links', 'governance')
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_org_runtime`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_gov_org_runtime`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_coverage_dedup`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_gov_coverage_dedup`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_record_dedup`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_gov_record_dedup`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_gov_record_dedup AS
    SELECT
      LOWER(COALESCE(NULLIF(r.rkey, ''), NULLIF(r.uri, ''), NULLIF(r.cid, ''), NULLIF(r.value_json, ''))) AS entity_key,
      MIN(r.uri) AS sample_uri,
      MIN(r.repo) AS repo,
      MIN(r.collection) AS sample_collection,
      CASE
        WHEN r.collection IN ('ai.gftd.apps.gov.entity', 'govOrgSiteDep') THEN 'admin_area'
        WHEN r.collection IN ('ai.gftd.apps.gov.agency', 'ai.gftd.apps.gov.ministry', 'govOrg', 'governanceContract') THEN 'government_org'
        ELSE 'other'
      END AS entity_kind,
      COUNT(*)::BIGINT AS duplicate_rows,
      MAX(r.indexed_at) AS latest_indexed_at
    FROM vertex_repo_record r
    WHERE r.collection IN (
      'ai.gftd.apps.gov.entity',
      'ai.gftd.apps.gov.agency',
      'ai.gftd.apps.gov.ministry',
      'govOrg',
      'govOrgSiteDep',
      'governanceContract'
    )
    GROUP BY
      LOWER(COALESCE(NULLIF(r.rkey, ''), NULLIF(r.uri, ''), NULLIF(r.cid, ''), NULLIF(r.value_json, ''))),
      CASE
        WHEN r.collection IN ('ai.gftd.apps.gov.entity', 'govOrgSiteDep') THEN 'admin_area'
        WHEN r.collection IN ('ai.gftd.apps.gov.agency', 'ai.gftd.apps.gov.ministry', 'govOrg', 'governanceContract') THEN 'government_org'
        ELSE 'other'
      END
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_gov_coverage_dedup AS
    SELECT
      SUM(CASE WHEN entity_kind = 'government_org' THEN 1 ELSE 0 END)::BIGINT AS government_org_count,
      SUM(CASE WHEN entity_kind = 'admin_area' THEN 1 ELSE 0 END)::BIGINT AS admin_area_count,
      SUM(duplicate_rows)::BIGINT AS source_rows,
      SUM(CASE WHEN duplicate_rows > 1 THEN duplicate_rows - 1 ELSE 0 END)::BIGINT AS duplicate_rows_removed,
      COUNT(*)::BIGINT AS dedup_entities
    FROM mv_gov_record_dedup
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_gov_org_runtime AS
    SELECT
      CONCAT('at://did:web:gov.etzhayyim.com/ai.gftd.apps.gov.orgRuntime/', runtime_key) AS vertex_id,
      entity_key AS gov_org_key,
      sample_uri AS source_uri,
      repo,
      sample_collection AS source_collection,
      CONCAT('did:web:gov.etzhayyim.com:org:', entity_key) AS actor_did,
      CONCAT('gov_org_', runtime_key, '_coverage_refresh') AS bpmn_process_id,
      CONCAT('at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/gov-org-', runtime_key, '-coverage-refresh-v1') AS bpmn_process_vertex_id,
      CONCAT('gov-org-', runtime_key, '-mcp') AS mcp_id,
      CONCAT('https://mcp.etzhayyim.com/mcp/gov/org/', runtime_key) AS mcp_endpoint,
      'ai.gftd.apps.gov.coverage.get,ai.gftd.apps.ingest.status,ai.gftd.apps.coverage.refresh' AS tool_nsids,
      'planned' AS status,
      latest_indexed_at
    FROM (
      SELECT
        *,
        REPLACE(REPLACE(entity_key, ':', '-'), '.', '-') AS runtime_key
      FROM mv_gov_record_dedup
    ) d
    WHERE entity_kind = 'government_org'
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`
    CREATE VIEW mv_world_coverage_live AS
    WITH gov_override AS (
      SELECT
        'gov'::VARCHAR AS domain,
        government_org_count AS record_count,
        (SELECT COUNT(*)::BIGINT FROM vertex_gov_org) AS vertex_count
      FROM mv_gov_coverage_dedup
      UNION ALL
      SELECT
        'gov_admin_area'::VARCHAR AS domain,
        admin_area_count AS record_count,
        (SELECT COUNT(*)::BIGINT FROM vertex_gov_municipality) AS vertex_count
      FROM mv_gov_coverage_dedup
    ),
    domain_counts AS (
      SELECT
        d.domain,
        d.app_host,
        d.world_total,
        d.unit,
        d.sector,
        COALESCE(p.did_count, 0)::BIGINT AS did_count,
        CASE
          WHEN go.domain IS NOT NULL THEN go.record_count
          ELSE COALESCE(r.record_count, 0)::BIGINT
        END AS record_count,
        CASE
          WHEN go.domain IS NOT NULL THEN go.vertex_count
          ELSE COALESCE(v.vertex_count, 0)::BIGINT
        END AS vertex_count
      FROM dim_world_domain d
      LEFT JOIN mv_world_did_per_host p ON p.app_host = d.app_host
      LEFT JOIN mv_world_record_per_host r ON r.app_host = d.app_host
      LEFT JOIN mv_world_vertex_per_host v ON v.app_host = d.app_host
      LEFT JOIN gov_override go ON go.domain = d.domain
    )
    SELECT
      domain,
      app_host,
      world_total,
      unit,
      sector,
      did_count,
      record_count,
      vertex_count,
      GREATEST(did_count, record_count, vertex_count) AS collected,
      CASE WHEN world_total > 0
        THEN GREATEST(did_count, record_count, vertex_count)::DOUBLE PRECISION / world_total::DOUBLE PRECISION
        ELSE 0.0
      END AS coverage_rate,
      CASE WHEN world_total > 0
        THEN 1.0 - GREATEST(did_count, record_count, vertex_count)::DOUBLE PRECISION / world_total::DOUBLE PRECISION
        ELSE 1.0
      END AS gap_rate,
      GREATEST(world_total - GREATEST(did_count, record_count, vertex_count), 0)::BIGINT AS remaining
    FROM domain_counts
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_world_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_org_runtime`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_gov_org_runtime`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_coverage_dedup`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_gov_coverage_dedup`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_record_dedup`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_gov_record_dedup`.execute(db);

  await sql`DELETE FROM dim_world_domain WHERE domain = 'gov_admin_area'`.execute(db);
  await sql`UPDATE dim_world_domain SET app_host = 'gov.etzhayyim.com', world_total = 500000, unit = 'government agencies (global)', sector = 'governance' WHERE domain = 'gov'`.execute(db);

  await sql`
    DELETE FROM dim_world_domain_collection
     WHERE domain IN ('gov', 'gov_admin_area')
        OR collection IN (
          'ai.gftd.apps.gov.entity',
          'ai.gftd.apps.gov.agency',
          'ai.gftd.apps.gov.ministry',
          'govOrg',
          'govOrgSiteDep',
          'governanceContract'
        )
  `.execute(db);

  await sql`
    INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES
      ('gov', 'gov', 'ai.gftd.apps.gov.entity', 500000, 'government agencies', 'governance'),
      ('gov', 'gov', 'ai.gftd.apps.gov.agency', 500000, 'government agencies', 'governance'),
      ('gov', 'gov', 'ai.gftd.apps.gov.ministry', 500000, 'government agencies', 'governance')
  `.execute(db);

  await sql`
    CREATE VIEW mv_world_coverage_live AS
    SELECT
      d.domain,
      d.app_host,
      d.world_total,
      d.unit,
      d.sector,
      COALESCE(p.did_count, 0) AS did_count,
      COALESCE(r.record_count, 0) AS record_count,
      COALESCE(v.vertex_count, 0) AS vertex_count,
      GREATEST(COALESCE(p.did_count, 0), COALESCE(r.record_count, 0), COALESCE(v.vertex_count, 0)) AS collected,
      CASE WHEN d.world_total > 0
        THEN GREATEST(COALESCE(p.did_count, 0), COALESCE(r.record_count, 0), COALESCE(v.vertex_count, 0))::DOUBLE PRECISION / d.world_total::DOUBLE PRECISION
        ELSE 0.0
      END AS coverage_rate,
      CASE WHEN d.world_total > 0
        THEN 1.0 - GREATEST(COALESCE(p.did_count, 0), COALESCE(r.record_count, 0), COALESCE(v.vertex_count, 0))::DOUBLE PRECISION / d.world_total::DOUBLE PRECISION
        ELSE 1.0
      END AS gap_rate,
      GREATEST(d.world_total - GREATEST(COALESCE(p.did_count, 0), COALESCE(r.record_count, 0), COALESCE(v.vertex_count, 0)), 0)::BIGINT AS remaining
    FROM dim_world_domain d
    LEFT JOIN mv_world_did_per_host p ON p.app_host = d.app_host
    LEFT JOIN mv_world_record_per_host r ON r.app_host = d.app_host
    LEFT JOIN mv_world_vertex_per_host v ON v.app_host = d.app_host
  `.execute(db);
}
