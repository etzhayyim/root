// tier: C
// L3 Capability registry (MCP binding + tool catalog).
//
// Two narrow tables:
//   vertex_kind_mcp_binding — one row per kind (=170 today), points
//     kagami.etzhayyim.com/{kind}/mcp to the real MCP endpoint. Walk-up lookup
//     by the kagami-resolver Worker (50-infra/.../kagami-resolver).
//   vertex_actor_capability — capability tag per actor (kind-inherited +
//     explicit overrides). Fed by declare-only today; LLM implicit
//     extraction (ADR draft 0061 §L3) deferred.
//
// No vector column: RisingWave 2.8.1 doesn't ship native `vector` yet.
// Discovery stays text-ILIKE (registry.findActor) until either:
//   (A) RW upgrade exposes native vector + IVF_PQ, OR
//   (B) client-side ANN over vertex_actor_embedding (export PQ8 to R2,
//       fetch top-K on demand).
//
// See 90-docs/260423-every-vertex-as-actor-design.md §L3.
import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Kind → MCP binding ──────────────────────────────────
  await sql`CREATE TABLE IF NOT EXISTS vertex_kind_mcp_binding (
    vertex_id       VARCHAR PRIMARY KEY,   -- = kind (e.g. 'page', 'maps_building')
    _seq            BIGINT,
    created_date    DATE,
    sensitivity_ord BIGINT,
    owner_did       VARCHAR,

    kind            VARCHAR NOT NULL,
    mcp_url         VARCHAR NOT NULL,      -- https://{kind}.etzhayyim.com/mcp
    description     VARCHAR,
    tools_json      VARCHAR,               -- cached tools/list snapshot (JSON array)
    tools_fetched_at VARCHAR,
    org_id          VARCHAR DEFAULT 'anon',
    user_id         VARCHAR DEFAULT 'anon',
    actor_id        VARCHAR DEFAULT '',
    created_at      VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_kind_mcp_binding_kind
    ON vertex_kind_mcp_binding(kind)`.execute(db);
  await sql`FLUSH`.execute(db);

  // ── Per-actor capability (kind-inherited default + overrides) ──
  await sql`CREATE TABLE IF NOT EXISTS vertex_actor_capability (
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
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_actor_capability_did
    ON vertex_actor_capability(did)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_actor_capability_tag
    ON vertex_actor_capability(tag)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_actor_capability_tag`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_actor_capability_did`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_actor_capability`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_vertex_kind_mcp_binding_kind`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kind_mcp_binding`.execute(db);
  await sql`FLUSH`.execute(db);
}
