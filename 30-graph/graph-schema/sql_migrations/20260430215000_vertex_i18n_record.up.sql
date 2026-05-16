CREATE TABLE vertex_i18n_record (
      vertex_id   VARCHAR PRIMARY KEY,
      _seq        BIGINT NOT NULL,
      owner_did   VARCHAR NOT NULL,
      record_id   VARCHAR NOT NULL,
      collection  VARCHAR NOT NULL,
      record_kind VARCHAR NOT NULL,
      record_json VARCHAR NOT NULL,
      created_at  TIMESTAMPTZ NOT NULL
    );

CREATE INDEX idx_vertex_i18n_record_collection ON vertex_i18n_record (collection, created_at DESC);

CREATE INDEX idx_vertex_i18n_record_kind ON vertex_i18n_record (record_kind, created_at DESC);
