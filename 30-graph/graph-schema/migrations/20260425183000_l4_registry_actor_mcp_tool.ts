import { Kysely, sql } from "kysely";

/**
 * L4 Registry SSoT — actor / MCP / tool registry tables.
 *
 * Per ADR-2604251830 (Shannon-Optimal 8-Layer Architecture), the L4 layer
 * holds the single source of truth for actor / MCP server / tool definitions.
 * CF Worker (L3 Dispatcher) reads these tables to resolve NSID → backend
 * routing decisions. `_app/meta` JSON and `actor-manifest.jsonld` files
 * become caches/generators of L4 rows (no longer authoritative).
 *
 * Naming: snake_case columns (DB-side convention per root CLAUDE.md
 * §Identifier naming). All three tables are not APPEND ONLY — registry
 * rows are mutable (deactivated_at flips, capability_tags grow). RisingWave
 * supports non-append-only PG tables for control-plane registries.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
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
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_actor_registry_backend_kind ON actor_registry(backend_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_actor_registry_tier ON actor_registry(tier)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS mcp_registry (
      mcp_id              VARCHAR PRIMARY KEY,
      endpoint            VARCHAR,
      auth_method         VARCHAR,
      tool_nsids          VARCHAR,
      actor_did           VARCHAR,
      last_health_check_at VARCHAR,
      created_at          VARCHAR,
      deactivated_at      VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_mcp_registry_actor_did ON mcp_registry(actor_did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS tool_registry (
      tool_nsid           VARCHAR PRIMARY KEY,
      execution_backend   VARCHAR,
      backend_ref         VARCHAR,
      governance_class    VARCHAR,
      approval_required   VARCHAR,
      actor_did           VARCHAR,
      created_at          VARCHAR,
      deactivated_at      VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_tool_registry_execution_backend ON tool_registry(execution_backend)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tool_registry_actor_did ON tool_registry(actor_did)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_tool_registry_actor_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_tool_registry_execution_backend`.execute(db);
  await sql`DROP TABLE IF EXISTS tool_registry`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mcp_registry_actor_did`.execute(db);
  await sql`DROP TABLE IF EXISTS mcp_registry`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_actor_registry_tier`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_actor_registry_backend_kind`.execute(db);
  await sql`DROP TABLE IF EXISTS actor_registry`.execute(db);
  await sql`FLUSH`.execute(db);
}
