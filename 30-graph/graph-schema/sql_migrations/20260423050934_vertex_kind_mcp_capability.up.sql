CREATE TABLE IF NOT EXISTS vertex_kind_mcp_binding (
    vertex_id       VARCHAR PRIMARY KEY,   -- = kind (e.g. 'page', 'maps_building')
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    kind            VARCHAR NOT NULL,
    mcp_url         VARCHAR NOT NULL,      -- https://{kind}.gftd.ai/mcp
    description     VARCHAR,
    tools_json      VARCHAR,               -- cached tools/list snapshot (JSON array)
    tools_fetched_at VARCHAR,
    org_id          VARCHAR DEFAULT 'anon',
    user_id         VARCHAR DEFAULT 'anon',
    actor_id        VARCHAR DEFAULT '',
    created_at      VARCHAR
  );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_kind_mcp_binding_kind
    ON vertex_kind_mcp_binding(kind);

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_actor_capability (
    vertex_id       VARCHAR PRIMARY KEY,   -- '{did}#{tag}' composite key
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    did             VARCHAR NOT NULL,      -- path-DID of the actor
    kind            VARCHAR,
    tag             VARCHAR NOT NULL,      -- 'nlp.translate', 'maps.geocode', ...
    descriptor      VARCHAR,               -- human text for discovery ranking
    confidence      REAL,                  -- 0..1
    source          VARCHAR,               -- 'inherited' | 'override' | 'implicit'
    org_id          VARCHAR DEFAULT 'anon',
    user_id         VARCHAR DEFAULT 'anon',
    actor_id        VARCHAR DEFAULT '',
    created_at      VARCHAR
  );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_actor_capability_did
    ON vertex_actor_capability(did);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_actor_capability_tag
    ON vertex_actor_capability(tag);

FLUSH;
