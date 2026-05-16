import type { Kysely } from "kysely";
import { sql } from "kysely";

const commonColumns = [
  ["record_key", "VARCHAR"],
  ["label", "VARCHAR"],
  ["status", "VARCHAR NOT NULL DEFAULT ''"],
  ["value_json", "TEXT"],
  ["indexed_at", "TIMESTAMP"],
  ["updated_at", "TIMESTAMP"],
  ["org_id", "VARCHAR"],
  ["user_id", "VARCHAR"],
  ["actor_id", "VARCHAR"],
  ["owner_did", "VARCHAR"],
  ["sensitivity_ord", "INTEGER NOT NULL DEFAULT 2"],
] as const;

async function addCommonColumns(db: Kysely<unknown>, table: string): Promise<void> {
  for (const [column, type] of commonColumns) {
    await sql`ALTER TABLE ${sql.table(table)} ADD COLUMN IF NOT EXISTS ${sql.ref(column)} ${sql.raw(type)}`.execute(db);
  }
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const table of ["vertex_handotai_source", "vertex_handotai_article", "vertex_handotai_digest"]) {
    await addCommonColumns(db, table);
  }

  await sql`ALTER TABLE vertex_handotai_source ADD COLUMN IF NOT EXISTS source_type VARCHAR NOT NULL DEFAULT 'rss'`.execute(db);
  await sql`ALTER TABLE vertex_handotai_source ADD COLUMN IF NOT EXISTS crawl_interval_min INTEGER NOT NULL DEFAULT 15`.execute(db);
  await sql`ALTER TABLE vertex_handotai_source ADD COLUMN IF NOT EXISTS writer_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_handotai_source ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP`.execute(db);

  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS subcategory VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS title_original VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS title_ja VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS title_en VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS summary_original VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS summary_ja VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS summary_en VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS entities_json TEXT`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS tags_json TEXT`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS sentiment VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS importance INTEGER NOT NULL DEFAULT 0`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS visibility VARCHAR NOT NULL DEFAULT 'free'`.execute(db);
  await sql`ALTER TABLE vertex_handotai_article ADD COLUMN IF NOT EXISTS writer_did VARCHAR`.execute(db);

  await sql`ALTER TABLE vertex_handotai_digest ADD COLUMN IF NOT EXISTS summary_ja TEXT`.execute(db);
  await sql`ALTER TABLE vertex_handotai_digest ADD COLUMN IF NOT EXISTS generated_at TIMESTAMP`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_handotai_collection_job (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT '',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      job_id VARCHAR NOT NULL,
      requested_at TIMESTAMP,
      started_at TIMESTAMP,
      finished_at TIMESTAMP,
      sources_count INTEGER NOT NULL DEFAULT 0,
      articles_count INTEGER NOT NULL DEFAULT 0
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_handotai_report (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT '',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      report_id VARCHAR NOT NULL,
      report_type VARCHAR NOT NULL DEFAULT 'weekly',
      entity_key VARCHAR,
      period VARCHAR,
      total_articles INTEGER NOT NULL DEFAULT 0,
      report_ja TEXT,
      generated_at TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_handotai_alert (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT '',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      alert_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      filter_categories_json TEXT,
      filter_entities_json TEXT,
      filter_keywords_json TEXT,
      filter_importance_min INTEGER NOT NULL DEFAULT 0,
      notify_channel VARCHAR,
      notify_email VARCHAR,
      tier VARCHAR NOT NULL DEFAULT 'free',
      enabled BOOLEAN NOT NULL DEFAULT true
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_handotai_subscription (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      sub_id VARCHAR NOT NULL,
      tier VARCHAR NOT NULL DEFAULT 'free',
      company_name VARCHAR,
      tracked_entities_json TEXT,
      started_at TIMESTAMP,
      expires_at TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_handotai_semi_entity (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      label VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      entity_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      entity_type VARCHAR NOT NULL DEFAULT 'company',
      country VARCHAR,
      segment VARCHAR,
      did VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_handotai_chip (
      vertex_id VARCHAR PRIMARY KEY,
      chip_id VARCHAR NOT NULL,
      name VARCHAR NOT NULL,
      manufacturer VARCHAR,
      product_family VARCHAR,
      source_url VARCHAR,
      source_title VARCHAR,
      source_domain VARCHAR,
      value_json TEXT,
      indexed_at TIMESTAMP,
      created_at TIMESTAMP,
      updated_at TIMESTAMP,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 300
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_handotai_source_article (
      edge_id VARCHAR PRIMARY KEY,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      source_id VARCHAR NOT NULL,
      article_id VARCHAR NOT NULL,
      relation VARCHAR NOT NULL DEFAULT 'published',
      created_at TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_handotai_article_entity (
      edge_id VARCHAR PRIMARY KEY,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      article_id VARCHAR NOT NULL,
      entity_key VARCHAR NOT NULL,
      relation VARCHAR NOT NULL DEFAULT 'mentions',
      created_at TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_handotai_subscription_entity (
      edge_id VARCHAR PRIMARY KEY,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      sub_id VARCHAR NOT NULL,
      entity_key VARCHAR NOT NULL,
      relation VARCHAR NOT NULL DEFAULT 'tracks',
      created_at TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_handotai_chip_source_page (
      edge_id VARCHAR PRIMARY KEY,
      from_vertex_id VARCHAR NOT NULL,
      to_vertex_id VARCHAR NOT NULL,
      chip_id VARCHAR NOT NULL,
      source_url VARCHAR,
      relation VARCHAR NOT NULL DEFAULT 'extracted_from',
      created_at TIMESTAMP
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_source_category_enabled ON vertex_handotai_source (category, enabled)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_source_writer_did ON vertex_handotai_source (writer_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_article_category ON vertex_handotai_article (category)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_article_source_name ON vertex_handotai_article (source_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_article_writer_did ON vertex_handotai_article (writer_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_alert_enabled_tier ON vertex_handotai_alert (enabled, tier)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_subscription_status_tier ON vertex_handotai_subscription (status, tier)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_semi_entity_type_country_segment ON vertex_handotai_semi_entity (entity_type, country, segment)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_chip_name ON vertex_handotai_chip (name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_chip_manufacturer ON vertex_handotai_chip (manufacturer)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_edge_source_article_source ON edge_handotai_source_article (source_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_edge_article_entity_key ON edge_handotai_article_entity (entity_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_handotai_edge_subscription_entity_key ON edge_handotai_subscription_entity (entity_key)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_handotai_article_category_counts AS
    SELECT category, COUNT(*) AS article_count, MAX(published_at) AS latest_published_at
    FROM vertex_handotai_article
    GROUP BY category
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_handotai_alert_status_counts AS
    SELECT enabled, tier, COUNT(*) AS alert_count
    FROM vertex_handotai_alert
    GROUP BY enabled, tier
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_handotai_subscription_tier_counts AS
    SELECT status, tier, COUNT(*) AS subscription_count
    FROM vertex_handotai_subscription
    GROUP BY status, tier
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_handotai_subscription_tier_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_handotai_alert_status_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_handotai_article_category_counts`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_handotai_chip_source_page`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_handotai_subscription_entity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_handotai_article_entity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_handotai_source_article`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_handotai_chip`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_handotai_semi_entity`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_handotai_subscription`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_handotai_alert`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_handotai_report`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_handotai_collection_job`.execute(db);
}
