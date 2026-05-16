CREATE TABLE vertex_apps_directory_record (
      vertex_id   VARCHAR PRIMARY KEY,
      _seq        BIGINT NOT NULL,
      owner_did   VARCHAR NOT NULL,
      record_id   VARCHAR NOT NULL,
      collection  VARCHAR NOT NULL,
      record_kind VARCHAR NOT NULL,
      app_did     VARCHAR,
      listing_id  VARCHAR,
      category    VARCHAR,
      record_json VARCHAR NOT NULL,
      created_at  TIMESTAMPTZ NOT NULL
    );

CREATE INDEX idx_vertex_apps_directory_collection ON vertex_apps_directory_record (collection, created_at DESC);

CREATE INDEX idx_vertex_apps_directory_listing ON vertex_apps_directory_record (listing_id, created_at DESC);

CREATE INDEX idx_vertex_apps_directory_category ON vertex_apps_directory_record (category, created_at DESC);
