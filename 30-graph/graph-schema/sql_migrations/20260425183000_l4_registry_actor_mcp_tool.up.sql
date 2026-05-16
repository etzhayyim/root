CREATE TABLE IF NOT EXISTS actor_registry (
      did                VARCHAR PRIMARY KEY,
      handle             VARCHAR,
      tier               VARCHAR,
      backend_kind       VARCHAR,
      backend_url        VARCHAR,
      capability_tags    VARCHAR,
      mcp_endpoint       VARCHAR,
      governance_class   VARCHAR,
      created_at         VARCHAR,
      deactivated_at     VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_actor_registry_backend_kind ON actor_registry(backend_kind);

CREATE INDEX IF NOT EXISTS idx_actor_registry_tier ON actor_registry(tier);

FLUSH;

CREATE TABLE IF NOT EXISTS mcp_registry (
      mcp_id              VARCHAR PRIMARY KEY,
      endpoint            VARCHAR,
      auth_method         VARCHAR,
      tool_nsids          VARCHAR,
      actor_did           VARCHAR,
      last_health_check_at VARCHAR,
      created_at          VARCHAR,
      deactivated_at      VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_mcp_registry_actor_did ON mcp_registry(actor_did);

FLUSH;

CREATE TABLE IF NOT EXISTS tool_registry (
      tool_nsid           VARCHAR PRIMARY KEY,
      execution_backend   VARCHAR,
      backend_ref         VARCHAR,
      governance_class    VARCHAR,
      approval_required   VARCHAR,
      actor_did           VARCHAR,
      created_at          VARCHAR,
      deactivated_at      VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_tool_registry_execution_backend ON tool_registry(execution_backend);

CREATE INDEX IF NOT EXISTS idx_tool_registry_actor_did ON tool_registry(actor_did);

FLUSH;
