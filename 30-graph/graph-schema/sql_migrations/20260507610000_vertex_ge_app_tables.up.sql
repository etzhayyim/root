CREATE TABLE IF NOT EXISTS vertex_ge_org (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      country VARCHAR,
      industry VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_ge_org_country ON vertex_ge_org (country);

CREATE INDEX IF NOT EXISTS idx_ge_org_status ON vertex_ge_org (status);

CREATE TABLE IF NOT EXISTS vertex_ge_project (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      org_id VARCHAR,
      name VARCHAR,
      description VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_ge_project_org_id ON vertex_ge_project (org_id);

CREATE INDEX IF NOT EXISTS idx_ge_project_status ON vertex_ge_project (status);

CREATE TABLE IF NOT EXISTS vertex_ge_resource_assignment (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      project_id VARCHAR,
      resource_did VARCHAR,
      role VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_ge_resource_project_id ON vertex_ge_resource_assignment (project_id);

CREATE INDEX IF NOT EXISTS idx_ge_resource_did ON vertex_ge_resource_assignment (resource_did);
