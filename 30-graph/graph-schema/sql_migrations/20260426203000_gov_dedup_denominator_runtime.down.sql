DROP MATERIALIZED VIEW IF EXISTS mv_world_coverage_live;

DROP VIEW IF EXISTS mv_world_coverage_live;

DROP MATERIALIZED VIEW IF EXISTS mv_gov_org_runtime;

DROP VIEW IF EXISTS mv_gov_org_runtime;

DROP MATERIALIZED VIEW IF EXISTS mv_gov_coverage_dedup;

DROP VIEW IF EXISTS mv_gov_coverage_dedup;

DROP MATERIALIZED VIEW IF EXISTS mv_gov_record_dedup;

DROP VIEW IF EXISTS mv_gov_record_dedup;

DELETE FROM dim_world_domain WHERE domain = 'gov_admin_area';

UPDATE dim_world_domain SET app_host = 'gov.gftd.ai', world_total = 500000, unit = 'government agencies (global)', sector = 'governance' WHERE domain = 'gov';

DELETE FROM dim_world_domain_collection
     WHERE domain IN ('gov', 'gov_admin_area')
        OR collection IN (
          'ai.gftd.apps.gov.entity',
          'ai.gftd.apps.gov.agency',
          'ai.gftd.apps.gov.ministry',
          'govOrg',
          'govOrgSiteDep',
          'governanceContract'
        );

INSERT INTO dim_world_domain_collection (domain, app_host, collection, world_total, unit, sector)
    VALUES
      ('gov', 'gov', 'ai.gftd.apps.gov.entity', 500000, 'government agencies', 'governance'),
      ('gov', 'gov', 'ai.gftd.apps.gov.agency', 500000, 'government agencies', 'governance'),
      ('gov', 'gov', 'ai.gftd.apps.gov.ministry', 500000, 'government agencies', 'governance');

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
    LEFT JOIN mv_world_vertex_per_host v ON v.app_host = d.app_host;
