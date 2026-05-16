import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_ffp_member (
      vertex_id VARCHAR PRIMARY KEY,
      member_id VARCHAR,
      member_number VARCHAR,
      member_did VARCHAR,
      first_name VARCHAR,
      last_name VARCHAR,
      email VARCHAR,
      nationality VARCHAR,
      tier VARCHAR,
      new_tier VARCHAR,
      previous_tier VARCHAR,
      qualifying_miles BIGINT,
      total_miles BIGINT,
      miles_balance BIGINT,
      miles_expiry_date VARCHAR,
      joined_at VARCHAR,
      enrolled_at VARCHAR,
      effective_date VARCHAR,
      carrier_code VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_ffp_miles_accrual (
      vertex_id VARCHAR PRIMARY KEY,
      txn_id VARCHAR,
      member_id VARCHAR,
      flight_no VARCHAR,
      dep_date VARCHAR,
      miles_earned BIGINT,
      partner_code VARCHAR,
      accrual_type VARCHAR,
      status VARCHAR,
      accrued_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_ffp_redemption (
      vertex_id VARCHAR PRIMARY KEY,
      redemption_id VARCHAR,
      member_id VARCHAR,
      reward_type VARCHAR,
      miles_used BIGINT,
      status VARCHAR,
      redeemed_at VARCHAR,
      partner_code VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_ffp_tier_event (
      vertex_id VARCHAR PRIMARY KEY,
      event_id VARCHAR,
      member_id VARCHAR,
      old_tier VARCHAR,
      new_tier VARCHAR,
      qualifying_miles BIGINT,
      effective_date VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_ffp_transaction (
      vertex_id VARCHAR PRIMARY KEY,
      member_number VARCHAR,
      from_member_number VARCHAR,
      to_member_number VARCHAR,
      flight_no VARCHAR,
      dep_date VARCHAR,
      miles_earned BIGINT,
      bonus_miles BIGINT,
      total_miles BIGINT,
      reward_code VARCHAR,
      miles_required BIGINT,
      current_balance BIGINT,
      sufficient BOOLEAN,
      redemption_ref VARCHAR,
      miles_amount BIGINT,
      transfer_ref VARCHAR,
      miles_purchased BIGINT,
      price_per_mile DOUBLE PRECISION,
      total_price DOUBLE PRECISION,
      payment_ref VARCHAR,
      miles_expired BIGINT,
      expiry_date VARCHAR,
      reason VARCHAR,
      partner_code VARCHAR,
      reconciliation_period VARCHAR,
      transaction_count BIGINT,
      currency VARCHAR,
      settlement_amount DOUBLE PRECISION,
      transaction_ref VARCHAR,
      transaction_type VARCHAR,
      status VARCHAR,
      reconciled_at VARCHAR,
      actor_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_air_member_has_accrual (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_ffp_member_id
      ON vertex_air_ffp_member (member_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_ffp_accrual_member_date
      ON vertex_air_ffp_miles_accrual (member_id, dep_date)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_ffp_member_tier_carrier
      ON vertex_air_ffp_member (tier, carrier_code)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_member_tier_summary AS
    SELECT
      carrier_code,
      tier,
      COUNT(*) AS member_count,
      AVG(total_miles) AS avg_total_miles
    FROM vertex_air_ffp_member
    WHERE status = 'active'
    GROUP BY carrier_code, tier
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_air_member_tier_summary`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_ffp_member_tier_carrier`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_ffp_accrual_member_date`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_ffp_member_id`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_member_has_accrual`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_ffp_transaction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_ffp_tier_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_ffp_redemption`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_ffp_miles_accrual`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_ffp_member`.execute(db);
}
