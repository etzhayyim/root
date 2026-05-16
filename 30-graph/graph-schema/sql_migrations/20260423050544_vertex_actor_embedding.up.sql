CREATE TABLE IF NOT EXISTS vertex_actor_embedding (
    vertex_id      VARCHAR PRIMARY KEY,
    _seq           BIGINT,
    created_date   DATE,
    sensitivity_ord BIGINT,
    owner_did      VARCHAR,

    did            VARCHAR,        -- path-DID from derive_did()
    kind           VARCHAR,        -- vertex_<kind> suffix
    embedding      VARCHAR,        -- 384 float32, comma-joined. VARCHAR until pgvector lands.
    embedding_norm REAL,           -- L2 norm (for cosine eval without recompute)
    model_id       VARCHAR,        -- 'multilingual-e5-small-v1' (tracks re-embed drift)
    embedded_at    VARCHAR,
    org_id         VARCHAR DEFAULT 'anon',
    user_id        VARCHAR DEFAULT 'anon',
    actor_id       VARCHAR DEFAULT '',
    created_at     VARCHAR
  );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_actor_embedding_kind
    ON vertex_actor_embedding(kind);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_actor_embedding_did
    ON vertex_actor_embedding(did);

FLUSH;
