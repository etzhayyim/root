CREATE TABLE IF NOT EXISTS vertex_api_key (
    vertex_id       VARCHAR PRIMARY KEY,
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    key_hash        VARCHAR,
    key_prefix      VARCHAR,
    name            VARCHAR,
    scopes          VARCHAR,
    status          VARCHAR,
    last_used_at    VARCHAR,
    created_at      VARCHAR
  );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_api_key_hash
    ON vertex_api_key(key_hash);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_api_key_owner
    ON vertex_api_key(owner_did);

FLUSH;
