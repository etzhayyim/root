// tier: C
// MCP tool registry as graph data (ADR-0087 amend, ADR-2604261000).
//
// Replaces the build-time codegen path (`70-tools/scripts/contract/
// gen-tool-manifest.mjs`) with a runtime DB-backed registry. Same
// `INSERT N rows` pattern as ADR-0056 BPMN-as-actor.
//
// One row per MCP-exposed tool. Source of truth is the lexicon JSON
// in `00-contracts/lexicons/com/etzhayyim/apps/**/*.json`; the
// `sync-mcp-registry.py` script upserts rows from disk on each
// `etzhayyim contract sync` run.
//
// host-sdk `/mcp` reads this table via Kysely + 60s in-memory cache
// to answer `tools/list`. `tools/call` validates `arguments` against
// `input_schema` (AJV runtime, JSON Schema 2020-12) and forwards to
// the existing `app.handleXRPC()` dispatch — no new dispatch path.
//
// Promoted columns only (no JSON column type — RW lacks JSONB; large
// JSON is stored as VARCHAR following the project convention).
//
// Vertex naming: `at://did:web:<actor-host>/com.etzhayyim.mcp.toolDef/<slug>`
// where slug = NSID with dots replaced by `-` (e.g.
// `etzhayyim-apps-yoro-listPosts`). Stable, content-addressable,
// queryable by actor_did via the secondary index.
//
// See: 90-docs/adr/2604261000-mcp-registry-via-kysely-schema.md,
//      90-docs/adr/0087-magatama-mcp-tool-facade.md (amended D3).
import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`CREATE TABLE IF NOT EXISTS vertex_mcp_tool_def (
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
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mcp_tool_def_nsid
    ON vertex_mcp_tool_def(nsid)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mcp_tool_def_actor_did
    ON vertex_mcp_tool_def(actor_did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_mcp_tool_def_enabled_actor
    ON vertex_mcp_tool_def(enabled, actor_did)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_mcp_tool_def_enabled_actor`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_mcp_tool_def_actor_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_mcp_tool_def_nsid`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_mcp_tool_def`.execute(db);
  await sql`FLUSH`.execute(db);
}
