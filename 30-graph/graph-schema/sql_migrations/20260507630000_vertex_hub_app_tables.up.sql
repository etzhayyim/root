CREATE TABLE IF NOT EXISTS vertex_hub_endpoint (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      url VARCHAR,
      method VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_hub_endpoint_status ON vertex_hub_endpoint (status);

CREATE TABLE IF NOT EXISTS vertex_hub_webhook (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      endpoint_id VARCHAR,
      target_url VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_hub_webhook_endpoint_id ON vertex_hub_webhook (endpoint_id);

CREATE INDEX IF NOT EXISTS idx_hub_webhook_status ON vertex_hub_webhook (status);
