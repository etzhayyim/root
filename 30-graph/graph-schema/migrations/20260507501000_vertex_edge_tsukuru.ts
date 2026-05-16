import type { Kysely } from "kysely";
import { sql } from "kysely";

const vertexTables = [
  "vertex_tsukuru_manufacturer",
  "vertex_tsukuru_factory",
  "vertex_tsukuru_production_order",
  "vertex_tsukuru_production_progress",
  "vertex_tsukuru_quality_inspection",
  "vertex_tsukuru_manufacturing_cell",
  "vertex_tsukuru_manufacturing_output",
  "vertex_tsukuru_software_integration",
  "vertex_tsukuru_logistics_route",
  "vertex_tsukuru_autonomy_operation",
  "vertex_tsukuru_supplier_exchange_package",
  "vertex_tsukuru_euv_manufacturing_flow",
  "vertex_tsukuru_certification",
];

const edgeTables = [
  "edge_tsukuru_manufacturer_factory",
  "edge_tsukuru_manufacturer_order",
  "edge_tsukuru_manufacturer_certification",
  "edge_tsukuru_order_progress",
  "edge_tsukuru_order_inspection",
  "edge_tsukuru_order_manufacturing_cell",
  "edge_tsukuru_order_manufacturing_output",
  "edge_tsukuru_order_supplier_package",
  "edge_tsukuru_order_euv_flow",
];

async function createVertexTable(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      vertex_key VARCHAR,
      label VARCHAR,
      status VARCHAR,
      value_json TEXT,
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
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_created_at`)} ON ${sql.table(table)} (created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_owner`)} ON ${sql.table(table)} (owner_did)`.execute(db);
}

async function createEdgeTable(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      edge_key VARCHAR,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      relation VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_key`)} ON ${sql.table(table)} (edge_key)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_relation`)} ON ${sql.table(table)} (relation)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const table of vertexTables) await createVertexTable(db, table);
  for (const table of edgeTables) await createEdgeTable(db, table);

  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS slug VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS legal_name VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS country_iso3 VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS category VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS industry_code VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS verification_tier VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS risk_tier VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_tsukuru_manufacturer ADD COLUMN IF NOT EXISTS onboarding_status VARCHAR`.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_country_category
      ON vertex_tsukuru_manufacturer (
        country_iso3,
        category
      )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_did ON vertex_tsukuru_manufacturer (did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_slug ON vertex_tsukuru_manufacturer (slug)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_industry_code ON vertex_tsukuru_manufacturer (industry_code)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_risk_tier ON vertex_tsukuru_manufacturer (risk_tier)`.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_tsukuru_manufacturer_onboarding_tier
      ON vertex_tsukuru_manufacturer (onboarding_status, verification_tier)
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_tsukuru_order_mfg_status
      ON vertex_tsukuru_production_order (
        (value_json::jsonb ->> 'manufacturerDid'),
        (value_json::jsonb ->> 'status')
      )
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_tsukuru_order_customer
      ON vertex_tsukuru_production_order ((value_json::jsonb ->> 'customerId'))
  `.execute(db);
  await sql`
    CREATE INDEX IF NOT EXISTS idx_tsukuru_inspection_order_result
      ON vertex_tsukuru_quality_inspection (
        (value_json::jsonb ->> 'productionOrderId'),
        (value_json::jsonb ->> 'result')
      )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tsukuru_platform_stats AS
    SELECT
      (SELECT count(*) FROM vertex_tsukuru_manufacturer) AS total_manufacturers,
      (SELECT count(*) FROM vertex_tsukuru_factory) AS total_factories,
      (SELECT count(*) FROM vertex_tsukuru_production_order) AS total_production_orders
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tsukuru_manufacturer_industry_counts AS
    SELECT industry_code, risk_tier, onboarding_status, count(*) AS cnt
    FROM vertex_tsukuru_manufacturer
    GROUP BY industry_code, risk_tier, onboarding_status
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_tsukuru_order_status_counts AS
    SELECT value_json::jsonb ->> 'status' AS status, count(*) AS cnt
    FROM vertex_tsukuru_production_order
    GROUP BY value_json::jsonb ->> 'status'
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_tsukuru_order_status_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_tsukuru_manufacturer_industry_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_tsukuru_platform_stats`.execute(db);
  for (const table of [...edgeTables].reverse()) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
  for (const table of [...vertexTables].reverse()) {
    await sql`DROP TABLE IF EXISTS ${sql.table(table)}`.execute(db);
  }
}
