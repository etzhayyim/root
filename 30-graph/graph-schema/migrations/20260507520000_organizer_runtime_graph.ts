import type { Kysely } from "kysely";
import { sql } from "kysely";

async function baseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR,
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
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_key`)} ON ${sql.table(table)} (record_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_status`)} ON ${sql.table(table)} (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_org`)} ON ${sql.table(table)} (org_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_indexed_at`)} ON ${sql.table(table)} (indexed_at)`.execute(db);
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
  await baseVertex(db, "vertex_organizer_item");
  await sql`ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS item_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS filename TEXT`.execute(db);
  await sql`ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS content_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS size_bytes DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS blake3 VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS blob_ref TEXT`.execute(db);
  await sql`ALTER TABLE vertex_organizer_item ADD COLUMN IF NOT EXISTS vault_did VARCHAR`.execute(db);

  await baseVertex(db, "vertex_organizer_classification");
  await sql`ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS classification_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS item_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS category VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS subcategory VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS model VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_classification ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION`.execute(db);

  await baseVertex(db, "vertex_organizer_tag");
  await sql`ALTER TABLE vertex_organizer_tag ADD COLUMN IF NOT EXISTS tag_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_tag ADD COLUMN IF NOT EXISTS item_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_tag ADD COLUMN IF NOT EXISTS name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_tag ADD COLUMN IF NOT EXISTS source VARCHAR`.execute(db);

  await baseVertex(db, "vertex_organizer_collection");
  await sql`ALTER TABLE vertex_organizer_collection ADD COLUMN IF NOT EXISTS collection_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_collection ADD COLUMN IF NOT EXISTS name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_collection ADD COLUMN IF NOT EXISTS description TEXT`.execute(db);
  await sql`ALTER TABLE vertex_organizer_collection ADD COLUMN IF NOT EXISTS visibility VARCHAR`.execute(db);

  await baseVertex(db, "vertex_organizer_rule");
  await sql`ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS rule_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS condition TEXT`.execute(db);
  await sql`ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS action VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS priority DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_organizer_rule ADD COLUMN IF NOT EXISTS target_collection_id VARCHAR`.execute(db);

  await baseVertex(db, "vertex_organizer_subscription_item");
  await sql`ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS subscription_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS sender VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS service_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS amount DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS currency VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS billing_cycle VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS first_seen_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS last_seen_at VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_item ADD COLUMN IF NOT EXISTS email_count BIGINT`.execute(db);

  await baseVertex(db, "vertex_organizer_subscription_analysis");
  await sql`ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS analysis_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS subscription_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS service_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS usage_score DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS cost_per_month DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS currency VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS recommendation VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_organizer_subscription_analysis ADD COLUMN IF NOT EXISTS analyzed_at VARCHAR`.execute(db);

  for (const table of [
    "vertex_organizer_item_deletion",
    "vertex_organizer_tag_deletion",
    "vertex_organizer_collection_item_deletion",
    "vertex_organizer_rule_deletion",
    "vertex_organizer_subscription_review_job",
    "vertex_organizer_subscription_item_update",
  ]) {
    await baseVertex(db, table);
  }

  await baseEdge(db, "edge_organizer_item_classification");
  await baseEdge(db, "edge_organizer_item_tag");
  await baseEdge(db, "edge_organizer_collection_item");
  await baseEdge(db, "edge_organizer_rule_collection");
  await baseEdge(db, "edge_organizer_subscription_analysis");
  await baseEdge(db, "edge_organizer_subscription_review_job");

  await sql`CREATE INDEX IF NOT EXISTS idx_organizer_item_vault ON vertex_organizer_item (org_id, vault_did, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_organizer_item_blake3 ON vertex_organizer_item (blake3)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_organizer_classification_category ON vertex_organizer_classification (org_id, category)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_organizer_tag_item ON vertex_organizer_tag (item_id, name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_organizer_collection_visibility ON vertex_organizer_collection (org_id, visibility)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_organizer_subscription_status ON vertex_organizer_subscription_item (org_id, status, billing_cycle)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_organizer_subscription_analysis_rec ON vertex_organizer_subscription_analysis (org_id, recommendation)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_organizer_item_status_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_organizer_item_status_counts AS
    SELECT org_id, vault_did, status, count(*)::BIGINT AS item_count, sum(size_bytes) AS total_bytes
    FROM vertex_organizer_item
    GROUP BY org_id, vault_did, status
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_organizer_classification_category_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_organizer_classification_category_counts AS
    SELECT org_id, category, subcategory, count(*)::BIGINT AS item_count, avg(confidence) AS avg_confidence
    FROM vertex_organizer_classification
    GROUP BY org_id, category, subcategory
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_organizer_subscription_monthly_cost`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_organizer_subscription_monthly_cost AS
    SELECT org_id, currency, status, count(*)::BIGINT AS subscription_count,
      sum(CASE billing_cycle WHEN 'yearly' THEN amount / 12 WHEN 'weekly' THEN amount * 4.33 ELSE amount END) AS monthly_cost
    FROM vertex_organizer_subscription_item
    GROUP BY org_id, currency, status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_organizer_subscription_monthly_cost`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_organizer_classification_category_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_organizer_item_status_counts`.execute(db);
  for (const table of [
    "edge_organizer_subscription_review_job",
    "edge_organizer_subscription_analysis",
    "edge_organizer_rule_collection",
    "edge_organizer_collection_item",
    "edge_organizer_item_tag",
    "edge_organizer_item_classification",
    "vertex_organizer_subscription_item_update",
    "vertex_organizer_subscription_review_job",
    "vertex_organizer_rule_deletion",
    "vertex_organizer_collection_item_deletion",
    "vertex_organizer_tag_deletion",
    "vertex_organizer_item_deletion",
    "vertex_organizer_subscription_analysis",
    "vertex_organizer_subscription_item",
    "vertex_organizer_rule",
    "vertex_organizer_collection",
    "vertex_organizer_tag",
    "vertex_organizer_classification",
    "vertex_organizer_item",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
