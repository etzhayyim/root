DROP VIEW IF EXISTS view_world_coverage_live;

DROP VIEW IF EXISTS mv_world_coverage_live;

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
    FROM domain_counts;

CREATE VIEW view_world_coverage_live AS SELECT * FROM mv_world_coverage_live;

GRANT SELECT ON mv_world_coverage_live TO root;

GRANT SELECT ON view_world_coverage_live TO root;

GRANT SELECT ON mv_world_coverage_live TO kaisya_app;

GRANT SELECT ON view_world_coverage_live TO kaisya_app;
