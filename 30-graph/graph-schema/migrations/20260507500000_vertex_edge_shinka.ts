import type { Kysely } from "kysely";
import { sql } from "kysely";

const vertexTables = [
  "vertex_shinka_timeline",
  "vertex_shinka_historical_event",
  "vertex_shinka_propagation_event",
  "vertex_shinka_propagation_job",
  "vertex_shinka_evolution_run",
  "vertex_shinka_kyumei_result",
  "vertex_shinka_coverage",
];

const edgeTables = [
  "edge_shinka_heard_from",
  "edge_shinka_mention",
  "edge_shinka_knowledge",
];

async function createVertexTable(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      vertex_key VARCHAR,
      label VARCHAR,
      status VARCHAR,
      value_json TEXT,
      indexed_at VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_key`)} ON ${sql.table(table)} (vertex_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_status`)} ON ${sql.table(table)} (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_indexed_at`)} ON ${sql.table(table)} (indexed_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_actor`)} ON ${sql.table(table)} (actor_did)`.execute(db);
}

async function createEdgeTable(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      edge_key VARCHAR,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      relation VARCHAR,
      label VARCHAR,
      status VARCHAR,
      value_json TEXT,
      indexed_at VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_key`)} ON ${sql.table(table)} (edge_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_relation`)} ON ${sql.table(table)} (relation)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_indexed_at`)} ON ${sql.table(table)} (indexed_at)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const table of vertexTables) await createVertexTable(db, table);
  for (const table of edgeTables) await createEdgeTable(db, table);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_shinka_job_status_schedule
      ON vertex_shinka_propagation_job (status, indexed_at)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_vertex_shinka_event_time
      ON vertex_shinka_propagation_event (created_at)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinka_propagation_queue_stats AS
    SELECT status, count(*) AS cnt
    FROM vertex_shinka_propagation_job
    GROUP BY status
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinka_knowledge_degree AS
    SELECT src_vid AS actor_did, count(*) AS out_degree
    FROM edge_shinka_knowledge
    GROUP BY src_vid
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shinka_knowledge_degree`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shinka_propagation_queue_stats`.execute(db);
  for (const table of [...edgeTables].reverse()) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
  for (const table of [...vertexTables].reverse()) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
