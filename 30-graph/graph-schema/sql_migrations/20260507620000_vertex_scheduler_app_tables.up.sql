CREATE TABLE IF NOT EXISTS vertex_scheduler_job (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      cron VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_scheduler_job_id ON vertex_scheduler_job (id);

CREATE INDEX IF NOT EXISTS idx_scheduler_job_status ON vertex_scheduler_job (status);
