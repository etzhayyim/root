CREATE TABLE IF NOT EXISTS vertex_tia_signal (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      signal_text VARCHAR,
      source VARCHAR,
      classification VARCHAR,
      risk_score DOUBLE PRECISION,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_tia_signal_id ON vertex_tia_signal (id);

CREATE INDEX IF NOT EXISTS idx_tia_signal_source ON vertex_tia_signal (source);

CREATE INDEX IF NOT EXISTS idx_tia_signal_classification ON vertex_tia_signal (classification);
