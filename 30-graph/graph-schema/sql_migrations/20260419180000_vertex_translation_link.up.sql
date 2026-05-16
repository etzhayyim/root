CREATE TABLE IF NOT EXISTS vertex_translation_link (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      source_uri       VARCHAR,
      source_lang      VARCHAR,
      translated_uri   VARCHAR,
      lang             VARCHAR,
      source           VARCHAR,
      quality_score    DOUBLE PRECISION,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_translation_link_source_uri ON vertex_translation_link (source_uri);

CREATE INDEX IF NOT EXISTS idx_vertex_translation_link_translated_uri ON vertex_translation_link (translated_uri);
