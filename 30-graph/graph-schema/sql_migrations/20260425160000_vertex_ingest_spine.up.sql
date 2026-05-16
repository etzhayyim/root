CREATE TABLE IF NOT EXISTS vertex_ingest_run (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      run_id VARCHAR NOT NULL,
      ingest_family VARCHAR NOT NULL,
      source_id VARCHAR NOT NULL,
      mode VARCHAR NOT NULL,
      status VARCHAR NOT NULL,

      zeebe_process_instance_key VARCHAR,
      bpmn_process_id VARCHAR,
      started_at VARCHAR,
      finished_at VARCHAR,
      requested_by VARCHAR,

      planned_shards BIGINT,
      completed_shards BIGINT,
      records_read BIGINT,
      records_written BIGINT,
      records_skipped BIGINT,
      error_count BIGINT,
      last_error VARCHAR,

      input_json VARCHAR,
      output_json VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      props VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_run_run_id ON vertex_ingest_run (run_id);

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_run_family_source ON vertex_ingest_run (ingest_family, source_id);

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_run_status_started ON vertex_ingest_run (status, started_at);

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_run_zeebe ON vertex_ingest_run (zeebe_process_instance_key);

CREATE TABLE IF NOT EXISTS vertex_ingest_cursor (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      ingest_family VARCHAR NOT NULL,
      source_id VARCHAR NOT NULL,
      shard_key VARCHAR NOT NULL,
      cursor_value VARCHAR,
      cursor_hash VARCHAR,
      high_watermark VARCHAR,
      content_hash VARCHAR,
      updated_at VARCHAR,
      locked_by_run_id VARCHAR,
      lock_expires_at VARCHAR,
      status VARCHAR,
      fail_count BIGINT,
      last_error VARCHAR,
      props VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_cursor_family_source ON vertex_ingest_cursor (ingest_family, source_id);

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_cursor_shard ON vertex_ingest_cursor (source_id, shard_key);

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_cursor_lock ON vertex_ingest_cursor (locked_by_run_id, lock_expires_at);

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_cursor_status ON vertex_ingest_cursor (status, updated_at);

CREATE TABLE IF NOT EXISTS vertex_ingest_artifact (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      run_id VARCHAR NOT NULL,
      artifact_kind VARCHAR NOT NULL,
      source_id VARCHAR NOT NULL,
      uri VARCHAR NOT NULL,
      sha256 VARCHAR,
      byte_size BIGINT,
      record_count BIGINT,
      created_at VARCHAR,
      props VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_artifact_run ON vertex_ingest_artifact (run_id);

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_artifact_source_kind ON vertex_ingest_artifact (source_id, artifact_kind);

CREATE INDEX IF NOT EXISTS idx_vertex_ingest_artifact_sha256 ON vertex_ingest_artifact (sha256);
