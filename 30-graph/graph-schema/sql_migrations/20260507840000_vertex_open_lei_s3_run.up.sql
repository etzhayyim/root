CREATE TABLE IF NOT EXISTS vertex_open_lei_s3_run (
      vertex_id            VARCHAR         PRIMARY KEY,
      created_date         DATE,
      sensitivity_ord      INT             DEFAULT 1,
      owner_did            VARCHAR,
      publish_date         DATE            NOT NULL,
      b2_bucket            VARCHAR,
      b2_key               VARCHAR,
      records_read         BIGINT          DEFAULT 0,
      records_written      BIGINT          DEFAULT 0,
      run_status           VARCHAR,
      error_msg            VARCHAR,
      started_at           TIMESTAMP WITH TIME ZONE,
      finished_at          TIMESTAMP WITH TIME ZONE,
      created_at           TIMESTAMP WITH TIME ZONE,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_open_lei_s3_run_publish_date
      ON vertex_open_lei_s3_run (publish_date);

CREATE INDEX IF NOT EXISTS idx_open_lei_s3_run_status
      ON vertex_open_lei_s3_run (run_status);
