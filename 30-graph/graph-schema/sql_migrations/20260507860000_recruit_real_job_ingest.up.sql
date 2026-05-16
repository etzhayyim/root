ALTER TABLE vertex_job_posting ADD COLUMN IF NOT EXISTS source_homepage VARCHAR;

CREATE TABLE IF NOT EXISTS vertex_recruit_job_ingest_run (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      rkey            VARCHAR,
      repo            VARCHAR,
      run_id          VARCHAR NOT NULL,
      platform        VARCHAR,
      status          VARCHAR,
      fetched         BIGINT,
      inserted        BIGINT,
      skipped         BIGINT,
      limit_count     BIGINT,
      batch_size      BIGINT,
      started_at      VARCHAR,
      finished_at     VARCHAR,
      duration_ms     BIGINT,
      error           VARCHAR,
      props           VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_job_posting_source_id ON vertex_job_posting (source, source_id);

CREATE INDEX IF NOT EXISTS idx_vertex_job_posting_ingested_at ON vertex_job_posting (ingested_at);

CREATE INDEX IF NOT EXISTS idx_recruit_job_ingest_run_started ON vertex_recruit_job_ingest_run (started_at);

CREATE INDEX IF NOT EXISTS idx_recruit_job_ingest_run_platform_status ON vertex_recruit_job_ingest_run (platform, status);
