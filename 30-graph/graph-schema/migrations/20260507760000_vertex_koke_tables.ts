import type { Kysely } from "kysely";
import { sql } from "kysely";

async function baseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_id VARCHAR,
      owner_did VARCHAR,
      label VARCHAR,
      status VARCHAR,
      stream_id VARCHAR,
      agent_did VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_record_id`)} ON ${sql.table(table)} (record_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_stream`)} ON ${sql.table(table)} (stream_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_agent`)} ON ${sql.table(table)} (agent_did)`.execute(db);
}

async function baseEdge(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  // koke (苔) — Layer 0 primary fixation vertex
  // Reversible capture of raw external signals (CO₂ → glucose).
  await baseVertex(db, "vertex_koke_fixation");
  await sql`ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS input_kind VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS raw_ref TEXT`.execute(db);
  await sql`ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS signal_hash VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS classification VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS fixed_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_koke_fixation ADD COLUMN IF NOT EXISTS released_at VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_koke_fixation_hash ON vertex_koke_fixation (signal_hash)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_koke_fixation_status ON vertex_koke_fixation (status)`.execute(db);

  // koke flow edge: fixation → hakkou ferment (handoff record)
  await baseEdge(db, "edge_koke_flow");
  await sql`ALTER TABLE edge_koke_flow ADD COLUMN IF NOT EXISTS fixation_id VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_koke_flow ADD COLUMN IF NOT EXISTS ferment_id VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_koke_flow ADD COLUMN IF NOT EXISTS handoff_kind VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_koke_flow ADD COLUMN IF NOT EXISTS handed_off_at VARCHAR`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_koke_flow`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_koke_fixation`.execute(db);
}
