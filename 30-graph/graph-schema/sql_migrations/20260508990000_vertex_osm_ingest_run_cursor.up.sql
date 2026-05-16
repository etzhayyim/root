CREATE TABLE IF NOT EXISTS vertex_osm_ingest_run (
      run_id           VARCHAR PRIMARY KEY,
      source_did       VARCHAR NOT NULL,
      pbf_url          VARCHAR,
      pbf_b2_key       VARCHAR,
      pbf_sha256       VARCHAR,
      pbf_size_bytes   BIGINT,
      started_at       TIMESTAMPTZ NOT NULL,
      completed_at     TIMESTAMPTZ,
      phase            VARCHAR NOT NULL DEFAULT 'init',
      nodes_total      BIGINT,
      ways_total       BIGINT,
      rels_total       BIGINT,
      nodes_written    BIGINT NOT NULL DEFAULT 0,
      ways_written     BIGINT NOT NULL DEFAULT 0,
      rel_rows_written BIGINT NOT NULL DEFAULT 0,
      rows_per_sec     DOUBLE PRECISION,
      status           VARCHAR NOT NULL DEFAULT 'running',
      error_msg        VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_osm_ingest_run_source_did ON vertex_osm_ingest_run (source_did);

CREATE INDEX IF NOT EXISTS idx_osm_ingest_run_status ON vertex_osm_ingest_run (status);

CREATE INDEX IF NOT EXISTS idx_osm_ingest_run_started_at ON vertex_osm_ingest_run (started_at);

CREATE TABLE IF NOT EXISTS vertex_osm_ingest_cursor (
      cursor_id    VARCHAR PRIMARY KEY,
      run_id       VARCHAR NOT NULL,
      source_did   VARCHAR NOT NULL,
      phase        VARCHAR NOT NULL,
      rows_written BIGINT NOT NULL DEFAULT 0,
      last_osm_id  BIGINT,
      updated_at   TIMESTAMPTZ NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_osm_ingest_cursor_run_id ON vertex_osm_ingest_cursor (run_id);

CREATE INDEX IF NOT EXISTS idx_osm_ingest_cursor_source_did ON vertex_osm_ingest_cursor (source_did);

CREATE TABLE IF NOT EXISTS vertex_osm_pbf_cache (
      cache_id       VARCHAR PRIMARY KEY,
      source_did     VARCHAR NOT NULL,
      geofabrik_url  VARCHAR NOT NULL,
      b2_key         VARCHAR NOT NULL,
      size_bytes     BIGINT NOT NULL,
      sha256         VARCHAR NOT NULL,
      cached_at      TIMESTAMPTZ NOT NULL,
      last_used_at   TIMESTAMPTZ NOT NULL,
      valid_date     VARCHAR NOT NULL
    );

CREATE INDEX IF NOT EXISTS idx_osm_pbf_cache_source_did ON vertex_osm_pbf_cache (source_did);

CREATE INDEX IF NOT EXISTS idx_osm_pbf_cache_valid_date ON vertex_osm_pbf_cache (valid_date);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_osm_ingest_recent AS
    SELECT
      run_id,
      source_did,
      phase,
      status,
      nodes_written,
      ways_written,
      rows_per_sec,
      started_at,
      completed_at
    FROM vertex_osm_ingest_run
    ORDER BY started_at DESC;
