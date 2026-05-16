ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS collection VARCHAR;

ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS source VARCHAR;

ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS source_id VARCHAR;

ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS ingested_at VARCHAR;

ALTER TABLE vertex_medical ADD COLUMN IF NOT EXISTS created_at VARCHAR;

CREATE TABLE IF NOT EXISTS vertex_medical_coverage_cursor (
      target_key VARCHAR PRIMARY KEY,
      cursor_value TEXT NOT NULL,
      records_ingested BIGINT,
      last_coverage_rate DOUBLE PRECISION,
      last_error TEXT,
      updated_at VARCHAR,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    );

CREATE TABLE IF NOT EXISTS edge_medical_source_record (
      edge_id VARCHAR PRIMARY KEY,
      source_id VARCHAR NOT NULL,
      record_vid VARCHAR NOT NULL,
      collection VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_medical_collection ON vertex_medical (collection);

CREATE INDEX IF NOT EXISTS idx_vertex_medical_code ON vertex_medical (code);

CREATE INDEX IF NOT EXISTS idx_vertex_medical_category ON vertex_medical (category);

CREATE INDEX IF NOT EXISTS idx_vertex_medical_source ON vertex_medical (source);

CREATE INDEX IF NOT EXISTS idx_vertex_medical_cursor_updated ON vertex_medical_coverage_cursor (updated_at);

CREATE INDEX IF NOT EXISTS idx_edge_medical_source_record_source ON edge_medical_source_record (source_id);

CREATE INDEX IF NOT EXISTS idx_edge_medical_source_record_record ON edge_medical_source_record (record_vid);

CREATE INDEX IF NOT EXISTS idx_edge_medical_source_record_collection ON edge_medical_source_record (collection);

DROP MATERIALIZED VIEW IF EXISTS mv_medical_record_count_by_collection;

CREATE MATERIALIZED VIEW mv_medical_record_count_by_collection AS
    SELECT collection, category, count(*)::BIGINT AS record_count, max(ingested_at) AS latest_ingested_at
    FROM vertex_medical
    WHERE collection IS NOT NULL AND collection <> ''
    GROUP BY collection, category;

DROP MATERIALIZED VIEW IF EXISTS mv_medical_record_count_by_source;

CREATE MATERIALIZED VIEW mv_medical_record_count_by_source AS
    SELECT source_id, collection, count(*)::BIGINT AS record_count, max(updated_at) AS latest_linked_at
    FROM edge_medical_source_record
    GROUP BY source_id, collection;

DROP MATERIALIZED VIEW IF EXISTS mv_world_collection_coverage_live;

DROP MATERIALIZED VIEW IF EXISTS mv_world_record_per_host_collection;

CREATE MATERIALIZED VIEW mv_world_record_per_host_collection AS
    WITH normalized AS (
      SELECT
        COALESCE(a.canonical_host, split_part(split_part(r.repo, 'did:web:', 2), '.', 1)) AS app_host,
        r.collection AS collection
      FROM vertex_repo_record r
      LEFT JOIN dim_app_host_alias a
        ON split_part(split_part(r.repo, 'did:web:', 2), '.', 1) = a.alias_host
      UNION ALL
      SELECT 'iryo' AS app_host, m.collection AS collection
      FROM vertex_medical m
      WHERE m.collection IS NOT NULL AND m.collection <> ''
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
