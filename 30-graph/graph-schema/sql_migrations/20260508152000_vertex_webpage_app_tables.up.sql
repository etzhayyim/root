CREATE TABLE IF NOT EXISTS vertex_webpage_page (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_webpage_page_status ON vertex_webpage_page (status);

CREATE TABLE IF NOT EXISTS vertex_webpage_publish (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      page_id VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_webpage_publish_page_id ON vertex_webpage_publish (page_id);

CREATE INDEX IF NOT EXISTS idx_webpage_publish_status ON vertex_webpage_publish (status);
