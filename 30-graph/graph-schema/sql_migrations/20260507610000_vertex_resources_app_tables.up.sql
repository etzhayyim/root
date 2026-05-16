CREATE TABLE IF NOT EXISTS vertex_resources_resource (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      kind VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_resources_resource_id ON vertex_resources_resource (id);

CREATE INDEX IF NOT EXISTS idx_resources_resource_kind ON vertex_resources_resource (kind);

CREATE INDEX IF NOT EXISTS idx_resources_resource_status ON vertex_resources_resource (status);

CREATE TABLE IF NOT EXISTS vertex_resources_allocation (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      resource_id VARCHAR,
      requester_did VARCHAR,
      quantity BIGINT,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_resources_allocation_id ON vertex_resources_allocation (id);

CREATE INDEX IF NOT EXISTS idx_resources_allocation_resource_id ON vertex_resources_allocation (resource_id);

CREATE INDEX IF NOT EXISTS idx_resources_allocation_status ON vertex_resources_allocation (status);
