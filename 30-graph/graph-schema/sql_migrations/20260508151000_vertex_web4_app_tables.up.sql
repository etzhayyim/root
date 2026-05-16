CREATE TABLE IF NOT EXISTS vertex_web4_expert (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      did VARCHAR,
      specialization VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_web4_expert_did ON vertex_web4_expert (did);

CREATE INDEX IF NOT EXISTS idx_web4_expert_status ON vertex_web4_expert (status);

CREATE TABLE IF NOT EXISTS vertex_web4_inference_job (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      expert_id VARCHAR,
      model VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_web4_inference_job_expert_id ON vertex_web4_inference_job (expert_id);

CREATE INDEX IF NOT EXISTS idx_web4_inference_job_status ON vertex_web4_inference_job (status);
