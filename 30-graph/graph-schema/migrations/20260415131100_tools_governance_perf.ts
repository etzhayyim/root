import { Kysely, sql } from "kysely";

/**
 * Performance + normalization support for tools/governance graph paths.
 *
 * Adds:
 * - composite indexes for vertex_capability / edge_capability / governance tables
 * - mv_actor_tool_grants: actor DID → granted tool projection
 * - mv_actor_governance_policy: actor DID → governance policy projection
 */
export async function up(db: Kysely<any>): Promise<void> {
  // Tool definition / grant lookup indexes
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_capability_collection_status_did_name
    ON vertex_capability (collection, status, did, name)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_capability_collection_status_worker_name
    ON vertex_capability (collection, status, capability_worker, name)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_capability_src_label_dst
    ON edge_capability (src_vid, label, dst_vid)
  `.execute(db);

  // Governance graph lookup indexes
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_governance_repo_kind_name
    ON vertex_governance (repo, kind, name)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_governance_src_label_dst
    ON edge_governance (src_vid, label, dst_vid)
  `.execute(db);

  // Actor grant projection (primary path for tools/list + tools/call auth).
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_tool_grants AS
    SELECT
      COALESCE(NULLIF(g.did, ''), g.repo) AS actor_did,
      g.name AS tool_name,
      CAST(g.created_date AS VARCHAR) AS granted_at,
      t.vertex_id AS tool_vertex_id,
      t.capability_worker AS capability_worker
    FROM vertex_capability g
    JOIN vertex_capability t
      ON t.name = g.name
     AND t.collection = 'ai.gftd.tool.tool'
     AND t.status = 'active'
    WHERE g.collection = 'ai.gftd.actor.toolGrant'
      AND g.status = 'active'
  `.execute(db);

  // Governance policy projection per actor DID.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_governance_policy AS
    SELECT
      e.src_vid AS actor_did,
      v.vertex_id AS policy_vid,
      v.name AS policy_name,
      v.kind AS kind,
      v.standard AS standard
    FROM edge_governance e
    JOIN vertex_governance v ON v.vertex_id = e.dst_vid
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_governance_policy`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_tool_grants`.execute(db);

  await sql`DROP INDEX IF EXISTS idx_edge_governance_src_label_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_governance_repo_kind_name`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_capability_src_label_dst`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_capability_collection_status_worker_name`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_capability_collection_status_did_name`.execute(db);
}
