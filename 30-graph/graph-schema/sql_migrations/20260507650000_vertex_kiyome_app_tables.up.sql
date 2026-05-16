CREATE TABLE IF NOT EXISTS vertex_kiyome_clearance (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      subject_did VARCHAR,
      clearance_type VARCHAR,
      description VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_kiyome_clearance_subject ON vertex_kiyome_clearance (subject_did);

CREATE INDEX IF NOT EXISTS idx_kiyome_clearance_status ON vertex_kiyome_clearance (status);

CREATE TABLE IF NOT EXISTS vertex_kiyome_audit_log (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      actor_did_ref VARCHAR,
      action VARCHAR,
      resource VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_kiyome_audit_log_actor ON vertex_kiyome_audit_log (actor_did_ref);
