CREATE TABLE IF NOT EXISTS vertex_satellite_scene (
      vertex_id          VARCHAR PRIMARY KEY,
      repo               VARCHAR NOT NULL,
      scene_id           VARCHAR,
      platform           VARCHAR,
      date_time          VARCHAR,
      cloud_cover        DOUBLE PRECISION,
      bbox               VARCHAR,
      stac_collection_id VARCHAR,
      stac_self_url      VARCHAR,
      source_did         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      created_at         VARCHAR,
      _seq               BIGINT,
      sensitivity_ord    INTEGER,
      owner_did          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_satellite_scene_repo
      ON vertex_satellite_scene (repo);

CREATE INDEX IF NOT EXISTS idx_satellite_scene_platform
      ON vertex_satellite_scene (platform);

CREATE INDEX IF NOT EXISTS idx_satellite_scene_date_time
      ON vertex_satellite_scene (date_time);

CREATE TABLE IF NOT EXISTS vertex_satellite_analysis (
      vertex_id       VARCHAR PRIMARY KEY,
      repo            VARCHAR NOT NULL,
      scene_uri       VARCHAR,
      analysis_type   VARCHAR,
      baseline_uri    VARCHAR,
      model_version   VARCHAR,
      summary         VARCHAR,
      confidence      DOUBLE PRECISION,
      ok              BOOLEAN,
      source_did      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      created_at      VARCHAR,
      _seq            BIGINT,
      sensitivity_ord INTEGER,
      owner_did       VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_satellite_analysis_repo
      ON vertex_satellite_analysis (repo);

CREATE INDEX IF NOT EXISTS idx_satellite_analysis_scene_uri
      ON vertex_satellite_analysis (scene_uri);

CREATE INDEX IF NOT EXISTS idx_satellite_analysis_type
      ON vertex_satellite_analysis (analysis_type);
