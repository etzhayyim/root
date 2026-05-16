DROP MATERIALIZED VIEW IF EXISTS mv_world_collection_coverage_live;

DROP MATERIALIZED VIEW IF EXISTS mv_world_record_per_host_collection;

DROP MATERIALIZED VIEW IF EXISTS mv_medical_record_count_by_source;

DROP MATERIALIZED VIEW IF EXISTS mv_medical_record_count_by_collection;

DROP TABLE IF EXISTS edge_medical_source_record;

CREATE MATERIALIZED VIEW mv_world_record_per_host_collection AS
    WITH normalized AS (
      SELECT
        COALESCE(a.canonical_host, split_part(split_part(r.repo, 'did:web:', 2), '.', 1)) AS app_host,
        r.collection AS collection
      FROM vertex_repo_record r
      LEFT JOIN dim_app_host_alias a
        ON split_part(split_part(r.repo, 'did:web:', 2), '.', 1) = a.alias_host
    )
    SELECT app_host, collection, COUNT(*)::BIGINT AS record_count
    FROM normalized
    GROUP BY app_host, collection;

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
      ON rc.app_host = d.app_host AND rc.collection = d.collection;
