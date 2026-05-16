CREATE TABLE IF NOT EXISTS vertex_isekai_world_map (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      name             VARCHAR,
      width_m          BIGINT,
      height_m         BIGINT,
      seed             BIGINT,
      biome_mask_cid   VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_isekai_world_scene (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      world_map_uri    VARCHAR,
      scene_type       VARCHAR,
      x_dm             BIGINT,
      z_dm             BIGINT,
      radius_dm        BIGINT,
      label            VARCHAR,
      params_json      VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_isekai_world_scene_map ON vertex_isekai_world_scene (world_map_uri);

CREATE INDEX IF NOT EXISTS idx_vertex_isekai_world_scene_type ON vertex_isekai_world_scene (scene_type);

CREATE TABLE IF NOT EXISTS vertex_isekai_world_portal (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      world_map_uri    VARCHAR,
      from_scene_uri   VARCHAR,
      to_scene_uri     VARCHAR,
      fade_ms          BIGINT,
      bidirectional    BOOLEAN,
      label            VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_map_contains_scene (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_map_contains_scene_src ON edge_map_contains_scene (src_vid);

CREATE TABLE IF NOT EXISTS edge_scene_adjacent (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      distance_dm        BIGINT,
      coupling_strength  DOUBLE PRECISION,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_scene_adjacent_src ON edge_scene_adjacent (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_scene_adjacent_dst ON edge_scene_adjacent (dst_vid);

CREATE TABLE IF NOT EXISTS edge_scene_portal (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      fade_ms          BIGINT,
      bidirectional    BOOLEAN,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_scene_portal_src ON edge_scene_portal (src_vid);
