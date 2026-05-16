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
  // newsletter — Newsletter Factory (ADR-2605072000)

  // Subscriber list (Tier 3 PII — sensitivity_ord=3)
  await baseVertex(db, "vertex_newsletter_subscriber");
  await sql`ALTER TABLE vertex_newsletter_subscriber ADD COLUMN IF NOT EXISTS email VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_subscriber ADD COLUMN IF NOT EXISTS subscriber_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_subscriber ADD COLUMN IF NOT EXISTS cohort_name VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_subscriber_email ON vertex_newsletter_subscriber (email)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_subscriber_cohort ON vertex_newsletter_subscriber (cohort_name)`.execute(db);

  // Campaign records
  await baseVertex(db, "vertex_newsletter_campaign");
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS campaign_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS campaign_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS topic TEXT`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS cohort_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS subject_line VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS body_html TEXT`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS quality_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS recipient_count BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS include_ad_slot BOOLEAN`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS ad_campaign_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_campaign ADD COLUMN IF NOT EXISTS sent_at VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_campaign_id ON vertex_newsletter_campaign (campaign_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_campaign_status ON vertex_newsletter_campaign (status)`.execute(db);

  // Open/click engagement events from Resend webhook (no PII — just aggregate counts)
  await baseVertex(db, "vertex_newsletter_engagement");
  await sql`ALTER TABLE vertex_newsletter_engagement ADD COLUMN IF NOT EXISTS campaign_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_engagement ADD COLUMN IF NOT EXISTS event_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_newsletter_engagement ADD COLUMN IF NOT EXISTS resend_email_id VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_engagement_campaign ON vertex_newsletter_engagement (campaign_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_newsletter_engagement_type ON vertex_newsletter_engagement (event_type)`.execute(db);

  // Campaign → subscriber send record
  await baseEdge(db, "edge_newsletter_sent");
  await sql`ALTER TABLE edge_newsletter_sent ADD COLUMN IF NOT EXISTS campaign_id VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_newsletter_sent ADD COLUMN IF NOT EXISTS subscriber_id VARCHAR`.execute(db);
  await sql`ALTER TABLE edge_newsletter_sent ADD COLUMN IF NOT EXISTS resend_email_id VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_newsletter_sent_campaign ON edge_newsletter_sent (campaign_id)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_newsletter_sent`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_newsletter_engagement`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_newsletter_campaign`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_newsletter_subscriber`.execute(db);
}
