CREATE TABLE IF NOT EXISTS vertex_ops_process_run (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      process_name VARCHAR,
      automation_id VARCHAR,
      trigger VARCHAR,
      status VARCHAR,
      started_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_ops_process_run_status ON vertex_ops_process_run (status);

CREATE INDEX IF NOT EXISTS idx_ops_process_run_automation_id ON vertex_ops_process_run (automation_id);

CREATE TABLE IF NOT EXISTS vertex_ops_automation (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      description VARCHAR,
      trigger_type VARCHAR,
      schedule VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_ops_automation_status ON vertex_ops_automation (status);

CREATE INDEX IF NOT EXISTS idx_ops_automation_trigger_type ON vertex_ops_automation (trigger_type);
