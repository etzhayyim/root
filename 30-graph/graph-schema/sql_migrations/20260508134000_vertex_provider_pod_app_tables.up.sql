CREATE TABLE IF NOT EXISTS vertex_provider_pod_provider (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      endpoint VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_provider_pod_provider_status ON vertex_provider_pod_provider (status);

CREATE INDEX IF NOT EXISTS idx_provider_pod_provider_actor_did ON vertex_provider_pod_provider (actor_did);

CREATE TABLE IF NOT EXISTS vertex_provider_pod_pod (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      provider_id VARCHAR,
      pod_name VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_provider_pod_pod_provider_id ON vertex_provider_pod_pod (provider_id);

CREATE INDEX IF NOT EXISTS idx_provider_pod_pod_status ON vertex_provider_pod_pod (status);

CREATE INDEX IF NOT EXISTS idx_provider_pod_pod_actor_did ON vertex_provider_pod_pod (actor_did);
