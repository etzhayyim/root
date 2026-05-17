CREATE TABLE IF NOT EXISTS vertex_copyright_ingest_state (
      registry         VARCHAR NOT NULL,
      cursor           VARCHAR,
      last_ingested_at VARCHAR,
      total_ingested   BIGINT  NOT NULL DEFAULT 0,
      last_post_count  BIGINT  NOT NULL DEFAULT 0,
      last_posted_at   VARCHAR,
      owner_did        VARCHAR NOT NULL DEFAULT 'did:web:copyright.etzhayyim.com',
      created_at       VARCHAR NOT NULL,
      updated_at       VARCHAR NOT NULL,
      PRIMARY KEY (registry)
    );
