CREATE TABLE IF NOT EXISTS vertex_worlds_scene (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      scene_type VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_worlds_scene_scene_type ON vertex_worlds_scene (scene_type);

CREATE INDEX IF NOT EXISTS idx_worlds_scene_status ON vertex_worlds_scene (status);

CREATE TABLE IF NOT EXISTS vertex_worlds_asset (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      asset_type VARCHAR,
      scene_id VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_worlds_asset_scene_id ON vertex_worlds_asset (scene_id);

CREATE INDEX IF NOT EXISTS idx_worlds_asset_asset_type ON vertex_worlds_asset (asset_type);

CREATE INDEX IF NOT EXISTS idx_worlds_asset_status ON vertex_worlds_asset (status);
