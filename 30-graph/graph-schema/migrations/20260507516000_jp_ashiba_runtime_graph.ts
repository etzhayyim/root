import type { Kysely } from "kysely";
import { sql } from "kysely";

async function createBaseVertex(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      vertex_id VARCHAR PRIMARY KEY,
      vertex_key VARCHAR,
      collection VARCHAR,
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
}

async function createBaseEdge(db: Kysely<unknown>, table: string): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
      edge_id VARCHAR PRIMARY KEY,
      edge_key VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation VARCHAR NOT NULL,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_relation`)} ON ${sql.table(table)} (relation)`.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await createBaseVertex(db, "vertex_jp_ashiba_rental_contract");
  await sql`ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS contract_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS customer_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS site_address VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS total_amount DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS deposit_amount DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS start_date VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_rental_contract ADD COLUMN IF NOT EXISTS end_date VARCHAR`.execute(db);

  await createBaseVertex(db, "vertex_jp_ashiba_subscription_plan");
  await sql`ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS subscription_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS customer_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS tier VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS monthly_fee DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS renewal_date VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_subscription_plan ADD COLUMN IF NOT EXISTS cancelled_at VARCHAR`.execute(db);

  await createBaseVertex(db, "vertex_jp_ashiba_site_schedule");
  await sql`ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS schedule_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS contract_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS task_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS scheduled_date VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_site_schedule ADD COLUMN IF NOT EXISTS assigned_crew_did VARCHAR`.execute(db);

  await createBaseVertex(db, "vertex_jp_ashiba_inspection");
  await sql`ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS inspection_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS contract_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS item_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS inspector_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS inspection_type VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS overall_result VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS severity VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_jp_ashiba_inspection ADD COLUMN IF NOT EXISTS inspected_at VARCHAR`.execute(db);

  await createBaseEdge(db, "edge_jp_ashiba_contract_schedule");
  await createBaseEdge(db, "edge_jp_ashiba_contract_inspection");
  await createBaseEdge(db, "edge_jp_ashiba_customer_contract");
  await createBaseEdge(db, "edge_jp_ashiba_customer_subscription");

  await sql`CREATE INDEX IF NOT EXISTS idx_jp_ashiba_contract_id ON vertex_jp_ashiba_rental_contract (contract_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_ashiba_contract_customer ON vertex_jp_ashiba_rental_contract (customer_did, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_ashiba_subscription_id ON vertex_jp_ashiba_subscription_plan (subscription_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_ashiba_subscription_customer ON vertex_jp_ashiba_subscription_plan (customer_did, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_ashiba_schedule_contract ON vertex_jp_ashiba_site_schedule (contract_id, scheduled_date)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_ashiba_inspection_contract ON vertex_jp_ashiba_inspection (contract_id, inspected_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_ashiba_inspection_result ON vertex_jp_ashiba_inspection (overall_result, severity)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_ashiba_contract_status_counts AS
    SELECT status, count(*) AS cnt, sum(coalesce(total_amount, 0)) AS total_amount_sum
    FROM vertex_jp_ashiba_rental_contract
    GROUP BY status
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_ashiba_subscription_tier_counts AS
    SELECT tier, status, count(*) AS cnt, sum(coalesce(monthly_fee, 0)) AS monthly_fee_sum
    FROM vertex_jp_ashiba_subscription_plan
    GROUP BY tier, status
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_ashiba_inspection_result_counts AS
    SELECT overall_result, severity, count(*) AS cnt
    FROM vertex_jp_ashiba_inspection
    GROUP BY overall_result, severity
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_ashiba_inspection_result_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_ashiba_subscription_tier_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_ashiba_contract_status_counts`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_ashiba_customer_subscription`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_ashiba_customer_contract`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_ashiba_contract_inspection`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_ashiba_contract_schedule`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_ashiba_inspection`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_ashiba_site_schedule`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_ashiba_subscription_plan`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_ashiba_rental_contract`.execute(db);
}
