import type { Kysely } from "kysely";
import { sql } from "kysely";

async function baseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      record_id VARCHAR,
      owner_did VARCHAR,
      listing_id VARCHAR,
      app_did VARCHAR,
      label VARCHAR,
      status VARCHAR,
      category VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_record_id`)} ON ${sql.table(table)} (record_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_listing`)} ON ${sql.table(table)} (listing_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_category`)} ON ${sql.table(table)} (category, created_at)`.execute(db);
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
  await baseVertex(db, "vertex_apps_directory_listing");
  await sql`ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS display_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS description TEXT`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS icon VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_listing ADD COLUMN IF NOT EXISTS embed_url TEXT`.execute(db);

  await baseVertex(db, "vertex_apps_directory_feature");
  await sql`ALTER TABLE vertex_apps_directory_feature ADD COLUMN IF NOT EXISTS feature_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_feature ADD COLUMN IF NOT EXISTS rail VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_feature ADD COLUMN IF NOT EXISTS rank BIGINT`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_feature ADD COLUMN IF NOT EXISTS approved_by_did VARCHAR`.execute(db);

  await baseVertex(db, "vertex_apps_directory_install_intent");
  await sql`ALTER TABLE vertex_apps_directory_install_intent ADD COLUMN IF NOT EXISTS intent_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_install_intent ADD COLUMN IF NOT EXISTS user_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_install_intent ADD COLUMN IF NOT EXISTS source VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_apps_directory_install_intent ADD COLUMN IF NOT EXISTS client VARCHAR`.execute(db);

  await baseEdge(db, "edge_apps_directory_listing_feature");
  await baseEdge(db, "edge_apps_directory_listing_install_intent");

  await sql`CREATE INDEX IF NOT EXISTS idx_apps_directory_listing_app_did ON vertex_apps_directory_listing (app_did, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_apps_directory_listing_status_category ON vertex_apps_directory_listing (status, category, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_apps_directory_feature_rail ON vertex_apps_directory_feature (rail, rank)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_apps_directory_install_user ON vertex_apps_directory_install_intent (user_did, created_at)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_apps_directory_category_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_apps_directory_category_counts AS
    SELECT category, status, count(*)::BIGINT AS listing_count
    FROM vertex_apps_directory_listing
    GROUP BY category, status
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_apps_directory_listing_engagement`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_apps_directory_listing_engagement AS
    SELECT l.listing_id, l.app_did, l.category,
      count(DISTINCT f.vertex_id)::BIGINT AS feature_count,
      count(DISTINCT i.vertex_id)::BIGINT AS install_intent_count
    FROM vertex_apps_directory_listing l
    LEFT JOIN vertex_apps_directory_feature f ON f.listing_id = l.listing_id
    LEFT JOIN vertex_apps_directory_install_intent i ON i.listing_id = l.listing_id
    GROUP BY l.listing_id, l.app_did, l.category
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_apps_directory_listing_engagement`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_apps_directory_category_counts`.execute(db);
  for (const table of [
    "edge_apps_directory_listing_install_intent",
    "edge_apps_directory_listing_feature",
    "vertex_apps_directory_install_intent",
    "vertex_apps_directory_feature",
    "vertex_apps_directory_listing",
  ]) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
