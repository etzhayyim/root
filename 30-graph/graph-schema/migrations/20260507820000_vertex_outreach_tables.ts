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
  // outreach — Sales Outreach Automation (ADR-2605072000)

  // Prospect list (Tier 3 PII — sensitivity_ord=3, ADR-0018)
  await baseVertex(db, "vertex_outreach_prospect");
  await sql`ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS email VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS prospect_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS title VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS company VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS cohort_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_prospect ADD COLUMN IF NOT EXISTS company_website VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_outreach_prospect_email ON vertex_outreach_prospect (email)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_outreach_prospect_cohort ON vertex_outreach_prospect (cohort_name)`.execute(db);

  // Outreach sequences
  await baseVertex(db, "vertex_outreach_sequence");
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS sequence_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS prospect_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS sequence_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS goal TEXT`.execute(db);
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS current_step BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS max_steps BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS reply_detected BOOLEAN`.execute(db);
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS include_sponsor_slot BOOLEAN`.execute(db);
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS ad_campaign_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_sequence ADD COLUMN IF NOT EXISTS zeebe_process_instance_key VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_outreach_sequence_id ON vertex_outreach_sequence (sequence_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_outreach_sequence_prospect ON vertex_outreach_sequence (prospect_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_outreach_sequence_status ON vertex_outreach_sequence (status)`.execute(db);

  // Per-step draft + send records
  await baseVertex(db, "vertex_outreach_step");
  await sql`ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS sequence_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS step_number BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS subject_line VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS body_text TEXT`.execute(db);
  await sql`ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS resend_email_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_step ADD COLUMN IF NOT EXISTS sent_at VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_outreach_step_sequence ON vertex_outreach_step (sequence_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_outreach_step_number ON vertex_outreach_step (sequence_id, step_number)`.execute(db);

  // Do Not Contact list (email only — no other PII stored)
  await baseVertex(db, "vertex_outreach_dnc");
  await sql`ALTER TABLE vertex_outreach_dnc ADD COLUMN IF NOT EXISTS email VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_outreach_dnc ADD COLUMN IF NOT EXISTS reason VARCHAR`.execute(db);
  await sql`CREATE UNIQUE INDEX IF NOT EXISTS idx_vertex_outreach_dnc_email ON vertex_outreach_dnc (email)`.execute(db);

  // Sequence → prospect send edge
  await baseEdge(db, "edge_outreach_sent");
  await sql`ALTER TABLE edge_outreach_sent ADD COLUMN IF NOT EXISTS sequence_id VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_outreach_sent ADD COLUMN IF NOT EXISTS prospect_id VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_outreach_sent ADD COLUMN IF NOT EXISTS step_number BIGINT`.execute(db);
  await sql`ALTER TABLE edge_outreach_sent ADD COLUMN IF NOT EXISTS resend_email_id VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_outreach_sent_sequence ON edge_outreach_sent (sequence_id)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_outreach_sent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_outreach_dnc`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_outreach_step`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_outreach_sequence`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_outreach_prospect`.execute(db);
}
