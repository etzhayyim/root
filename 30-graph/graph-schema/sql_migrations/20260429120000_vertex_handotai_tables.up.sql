CREATE TABLE IF NOT EXISTS vertex_handotai_source (
      vertex_id     VARCHAR PRIMARY KEY,
      source_id     VARCHAR NOT NULL,
      name          VARCHAR NOT NULL,
      url           VARCHAR NOT NULL,
      language      VARCHAR NOT NULL DEFAULT 'ja',
      category      VARCHAR NOT NULL DEFAULT 'general',
      enabled       BOOLEAN NOT NULL DEFAULT true,
      last_fetched_at TIMESTAMP,
      actor_did     VARCHAR NOT NULL,
      org_did       VARCHAR NOT NULL,
      created_at    TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_handotai_source_source_id
      ON vertex_handotai_source (source_id);

CREATE TABLE IF NOT EXISTS vertex_handotai_article (
      vertex_id       VARCHAR PRIMARY KEY,
      article_id      VARCHAR NOT NULL,
      source_id       VARCHAR NOT NULL,
      source_name     VARCHAR NOT NULL,
      source_lang     VARCHAR NOT NULL DEFAULT 'ja',
      source_url      VARCHAR NOT NULL,
      title           VARCHAR,
      summary         VARCHAR,
      category        VARCHAR NOT NULL DEFAULT 'general',
      published_at    TIMESTAMP,
      crawled_at      TIMESTAMP,
      actor_did       VARCHAR NOT NULL,
      org_did         VARCHAR NOT NULL,
      created_at      TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_handotai_article_article_id
      ON vertex_handotai_article (article_id);

CREATE INDEX IF NOT EXISTS idx_handotai_article_source_id
      ON vertex_handotai_article (source_id);

CREATE INDEX IF NOT EXISTS idx_handotai_article_published_at
      ON vertex_handotai_article (published_at);

CREATE TABLE IF NOT EXISTS vertex_handotai_digest (
      vertex_id       VARCHAR PRIMARY KEY,
      digest_date     VARCHAR NOT NULL,
      article_count   BIGINT NOT NULL DEFAULT 0,
      summary         VARCHAR,
      key_topics      VARCHAR,
      actor_did       VARCHAR NOT NULL,
      org_did         VARCHAR NOT NULL,
      created_at      TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_handotai_digest_date
      ON vertex_handotai_digest (digest_date);
