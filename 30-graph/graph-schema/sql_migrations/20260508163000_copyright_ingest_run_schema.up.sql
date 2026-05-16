CREATE TABLE IF NOT EXISTS vertex_copyright_ingest_run (
      vertex_id       VARCHAR PRIMARY KEY,
      owner_did       VARCHAR NOT NULL,
      registry        VARCHAR NOT NULL,
      started_at      VARCHAR,
      finished_at     VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'running',
      rows_fetched    BIGINT DEFAULT 0,
      rows_inserted   BIGINT DEFAULT 0,
      error           VARCHAR,
      created_date    DATE,
      sensitivity_ord BIGINT DEFAULT 0
    );

CREATE INDEX idx_copyright_ingest_run_registry
      ON vertex_copyright_ingest_run(registry);

CREATE INDEX idx_copyright_ingest_run_status
      ON vertex_copyright_ingest_run(status);

CREATE INDEX idx_copyright_ingest_run_started_at
      ON vertex_copyright_ingest_run(started_at);

CREATE TABLE IF NOT EXISTS edge_work_blob_of (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR NOT NULL,
      dst_vid         VARCHAR NOT NULL,
      owner_did       VARCHAR,
      created_date    DATE,
      sensitivity_ord BIGINT DEFAULT 0
    );

CREATE INDEX idx_edge_work_blob_of_src
      ON edge_work_blob_of(src_vid);

CREATE INDEX idx_edge_work_blob_of_dst
      ON edge_work_blob_of(dst_vid);
