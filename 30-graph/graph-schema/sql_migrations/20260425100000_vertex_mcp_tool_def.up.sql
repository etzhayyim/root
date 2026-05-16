CREATE TABLE IF NOT EXISTS vertex_mcp_tool_def (
    vertex_id        VARCHAR PRIMARY KEY,
    _seq             BIGINT,
    created_date     DATE,
    sensitivity_ord  BIGINT,
    owner_did        VARCHAR,

    nsid             VARCHAR NOT NULL,
    actor_did        VARCHAR NOT NULL,
    actor_host       VARCHAR,
    lexicon_type     VARCHAR,
    description      VARCHAR,
    input_schema     VARCHAR,
    output_schema    VARCHAR,
    lxm_scope        VARCHAR,
    visibility       VARCHAR DEFAULT 'public',
    version          INT     DEFAULT 1,
    enabled          BOOLEAN DEFAULT TRUE,
    source_path      VARCHAR,
    schema_hash      VARCHAR,
    deployed_at      VARCHAR,

    org_id           VARCHAR DEFAULT 'anon',
    user_id          VARCHAR DEFAULT 'anon',
    actor_id         VARCHAR DEFAULT '',
    created_at       VARCHAR
  );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_mcp_tool_def_nsid
    ON vertex_mcp_tool_def(nsid);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_mcp_tool_def_actor_did
    ON vertex_mcp_tool_def(actor_did);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_mcp_tool_def_enabled_actor
    ON vertex_mcp_tool_def(enabled, actor_did);

FLUSH;
