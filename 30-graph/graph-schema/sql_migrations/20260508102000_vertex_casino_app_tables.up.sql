CREATE TABLE IF NOT EXISTS vertex_casino_casino (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      city VARCHAR,
      country VARCHAR,
      license_status VARCHAR,
      description VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_casino_casino_city ON vertex_casino_casino (city);

CREATE INDEX IF NOT EXISTS idx_casino_casino_country ON vertex_casino_casino (country);

CREATE TABLE IF NOT EXISTS vertex_casino_review (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      casino_id VARCHAR,
      reviewer_did VARCHAR,
      rating BIGINT,
      content VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_casino_review_casino_id ON vertex_casino_review (casino_id);

CREATE INDEX IF NOT EXISTS idx_casino_review_reviewer ON vertex_casino_review (reviewer_did);
