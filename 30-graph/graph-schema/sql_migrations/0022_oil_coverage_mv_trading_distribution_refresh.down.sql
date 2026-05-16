DROP MATERIALIZED VIEW IF EXISTS mv_oil_coverage_live;

DROP MATERIALIZED VIEW IF EXISTS mv_oil_backbone_count;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_oil_backbone_count AS
    SELECT country_code, 'upstream'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_field
    GROUP BY country_code

    UNION ALL

    SELECT COALESCE(split_part(locode, '-', 1), 'ZZ') AS country_code, 'midstream'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_terminal
    GROUP BY COALESCE(split_part(locode, '-', 1), 'ZZ')

    UNION ALL

    SELECT country_code, 'refining'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_refinery
    GROUP BY country_code

    UNION ALL

    SELECT hq_country AS country_code, 'trading'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_company
    WHERE company_type = 'trader'
    GROUP BY hq_country

    UNION ALL

    SELECT COALESCE(split_part(load_port, '-', 1), 'ZZ') AS country_code, 'shipping'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_cargo
    GROUP BY COALESCE(split_part(load_port, '-', 1), 'ZZ')

    UNION ALL

    SELECT country_code, 'distribution'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_refinery
    GROUP BY country_code;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_oil_coverage_live AS
    SELECT
      t.target_key,
      t.country_code,
      t.segment,
      t.actor_did,
      t.app,
      t.target_count,
      t.priority,
      COALESCE(b.actual_count, 0) AS actual_count,
      CASE
        WHEN t.target_count > 0 THEN COALESCE(b.actual_count, 0)::double precision / t.target_count::double precision
        ELSE 0.0
      END AS coverage_rate,
      GREATEST(t.target_count - COALESCE(b.actual_count, 0), 0) AS coverage_gap
    FROM dim_oil_coverage_target t
    LEFT JOIN mv_oil_backbone_count b
      ON b.country_code = t.country_code
     AND b.segment = t.segment;
