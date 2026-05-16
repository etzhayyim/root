CREATE TABLE IF NOT EXISTS vertex_maps_building_3d (
      vertex_id         VARCHAR PRIMARY KEY,
      spatial_vertex_id VARCHAR,
      tile_h3           VARCHAR NOT NULL,
      h3_resolution     BIGINT,
      centroid_lat      DOUBLE PRECISION,
      centroid_lng      DOUBLE PRECISION,
      footprint_json    VARCHAR,
      height_m          DOUBLE PRECISION,
      source            VARCHAR NOT NULL,
      mesh_uri          VARCHAR,
      coverage_score    DOUBLE PRECISION,
      ingest_at         VARCHAR,
      created_at        VARCHAR,
      sensitivity_ord   BIGINT,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      owner_did         VARCHAR,
      _seq              BIGINT
    );

CREATE INDEX IF NOT EXISTS idx_maps_building_3d_tile_h3
      ON vertex_maps_building_3d (tile_h3);

CREATE INDEX IF NOT EXISTS idx_maps_building_3d_spatial_vid
      ON vertex_maps_building_3d (spatial_vertex_id);

CREATE INDEX IF NOT EXISTS idx_maps_building_3d_source
      ON vertex_maps_building_3d (source, ingest_at);

CREATE TABLE IF NOT EXISTS vertex_maps_building_coverage (
      vertex_id         VARCHAR PRIMARY KEY,
      tile_h3           VARCHAR NOT NULL,
      h3_resolution     BIGINT,
      centroid_lat      DOUBLE PRECISION,
      centroid_lng      DOUBLE PRECISION,
      building_count    BIGINT,
      has_sentinel      BOOLEAN,
      has_mapraly       BOOLEAN,
      coverage_source   VARCHAR,
      last_ingest_at    VARCHAR,
      status            VARCHAR NOT NULL,
      created_at        VARCHAR,
      sensitivity_ord   BIGINT,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      owner_did         VARCHAR,
      _seq              BIGINT
    );

CREATE INDEX IF NOT EXISTS idx_maps_building_coverage_tile
      ON vertex_maps_building_coverage (tile_h3);

CREATE INDEX IF NOT EXISTS idx_maps_building_coverage_status
      ON vertex_maps_building_coverage (status, last_ingest_at);
