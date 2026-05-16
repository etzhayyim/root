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
  // webmk — Web Marketing Proposal Agent (ADR-2605072000)

  // Client records: one per website being analyzed
  await baseVertex(db, "vertex_webmk_client");
  await sql`ALTER TABLE vertex_webmk_client ADD COLUMN IF NOT EXISTS client_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_webmk_client ADD COLUMN IF NOT EXISTS website_url VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_webmk_client ADD COLUMN IF NOT EXISTS industry VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_webmk_client ADD COLUMN IF NOT EXISTS delivery_email VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_webmk_client_url ON vertex_webmk_client (website_url)`.execute(db);

  // Proposal records: one per createProposal request
  await baseVertex(db, "vertex_webmk_proposal");
  await sql`ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS client_vid VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS proposal_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS budget_jpy BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS strategy_json TEXT`.execute(db);
  await sql`ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS copy_markdown TEXT`.execute(db);
  await sql`ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS lg_run_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_webmk_proposal ADD COLUMN IF NOT EXISTS delivered_at VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_webmk_proposal_id ON vertex_webmk_proposal (proposal_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_webmk_proposal_status ON vertex_webmk_proposal (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_webmk_proposal_client ON vertex_webmk_proposal (client_vid)`.execute(db);

  // Campaign link: proposal → ads.gftd.ai campaign
  await baseEdge(db, "edge_webmk_campaign_link");
  await sql`ALTER TABLE edge_webmk_campaign_link ADD COLUMN IF NOT EXISTS proposal_id VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_webmk_campaign_link ADD COLUMN IF NOT EXISTS ads_campaign_id VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_webmk_campaign_link ADD COLUMN IF NOT EXISTS ads_campaign_did VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_webmk_campaign_proposal ON edge_webmk_campaign_link (proposal_id)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_webmk_campaign_link`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webmk_proposal`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webmk_client`.execute(db);
}
