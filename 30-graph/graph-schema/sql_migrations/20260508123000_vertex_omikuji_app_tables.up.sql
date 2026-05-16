CREATE TABLE IF NOT EXISTS vertex_omikuji_fortune_draw (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      shrine_id VARCHAR,
      user_did VARCHAR,
      result VARCHAR,
      drawn_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_omikuji_fortune_draw_shrine_id ON vertex_omikuji_fortune_draw (shrine_id);

CREATE INDEX IF NOT EXISTS idx_omikuji_fortune_draw_user_did ON vertex_omikuji_fortune_draw (user_did);

CREATE TABLE IF NOT EXISTS vertex_omikuji_shrine (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      location VARCHAR,
      description VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_omikuji_shrine_status ON vertex_omikuji_shrine (status);

CREATE INDEX IF NOT EXISTS idx_omikuji_shrine_location ON vertex_omikuji_shrine (location);
