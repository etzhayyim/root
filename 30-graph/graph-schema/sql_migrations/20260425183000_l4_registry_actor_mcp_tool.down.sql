DROP INDEX IF EXISTS idx_tool_registry_actor_did;

DROP INDEX IF EXISTS idx_tool_registry_execution_backend;

DROP TABLE IF EXISTS tool_registry;

DROP INDEX IF EXISTS idx_mcp_registry_actor_did;

DROP TABLE IF EXISTS mcp_registry;

DROP INDEX IF EXISTS idx_actor_registry_tier;

DROP INDEX IF EXISTS idx_actor_registry_backend_kind;

DROP TABLE IF EXISTS actor_registry;

FLUSH;
