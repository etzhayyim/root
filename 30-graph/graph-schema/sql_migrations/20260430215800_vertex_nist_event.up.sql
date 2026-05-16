CREATE TABLE vertex_nist_event (
      vertex_id   VARCHAR PRIMARY KEY,
      _seq        BIGINT NOT NULL,
      owner_did   VARCHAR NOT NULL,
      event_id    VARCHAR NOT NULL,
      event_kind  VARCHAR NOT NULL,
      event_json  VARCHAR NOT NULL,
      created_at  TIMESTAMPTZ NOT NULL
    );

CREATE INDEX idx_vertex_nist_event_kind ON vertex_nist_event (event_kind, created_at DESC);
