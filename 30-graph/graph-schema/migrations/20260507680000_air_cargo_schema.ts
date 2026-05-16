import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_cargo_awb (
      vertex_id VARCHAR PRIMARY KEY,
      awb_no VARCHAR,
      awb_number VARCHAR,
      booking_ref VARCHAR,
      shipper_did VARCHAR,
      shipper_name VARCHAR,
      consignee_did VARCHAR,
      consignee_name VARCHAR,
      origin VARCHAR,
      dest VARCHAR,
      origin_iata VARCHAR,
      dest_iata VARCHAR,
      weight_kg DOUBLE PRECISION,
      chargeable_weight_kg DOUBLE PRECISION,
      pieces BIGINT,
      currency VARCHAR,
      commodity_code VARCHAR,
      commodity VARCHAR,
      is_dangerous_goods BOOLEAN,
      status VARCHAR,
      issued_at VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_cargo_uld (
      vertex_id VARCHAR PRIMARY KEY,
      uld_no VARCHAR,
      uld_type VARCHAR,
      aircraft_reg VARCHAR,
      last_seen_at VARCHAR,
      status VARCHAR,
      tare_kg DOUBLE PRECISION,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_cargo_booking (
      vertex_id VARCHAR PRIMARY KEY,
      booking_id VARCHAR,
      booking_ref VARCHAR,
      awb_no VARCHAR,
      awb_number VARCHAR,
      flight_no VARCHAR,
      dep_date VARCHAR,
      carrier_code VARCHAR,
      origin VARCHAR,
      dest VARCHAR,
      origin_iata VARCHAR,
      dest_iata VARCHAR,
      pieces BIGINT,
      weight_kg DOUBLE PRECISION,
      actual_weight_kg DOUBLE PRECISION,
      rate DOUBLE PRECISION,
      currency VARCHAR,
      commodity VARCHAR,
      special_handling VARCHAR,
      uld_number VARCHAR,
      awb_numbers TEXT,
      loaded_weight_kg DOUBLE PRECISION,
      position VARCHAR,
      event_type VARCHAR,
      event_station VARCHAR,
      event_time VARCHAR,
      claim_ref VARCHAR,
      claim_type VARCHAR,
      claim_amount DOUBLE PRECISION,
      description TEXT,
      screening_ref VARCHAR,
      method VARCHAR,
      result VARCHAR,
      status VARCHAR,
      accepted_at VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_cargo_claim (
      vertex_id VARCHAR PRIMARY KEY,
      claim_id VARCHAR,
      awb_no VARCHAR,
      claim_type VARCHAR,
      amount DOUBLE PRECISION,
      currency VARCHAR,
      status VARCHAR,
      filed_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_cargo_cass_settlement (
      vertex_id VARCHAR PRIMARY KEY,
      agent_code VARCHAR,
      settlement_period VARCHAR,
      awb_count BIGINT,
      gross_amount DOUBLE PRECISION,
      net_amount DOUBLE PRECISION,
      currency VARCHAR,
      status VARCHAR,
      settled_at VARCHAR,
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
    CREATE TABLE IF NOT EXISTS edge_air_awb_loaded_in_uld (
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
    CREATE INDEX IF NOT EXISTS idx_air_cargo_awb_no
      ON vertex_air_cargo_awb (awb_no)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_cargo_uld_no
      ON vertex_air_cargo_uld (uld_no)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_cargo_booking_flight_date
      ON vertex_air_cargo_booking (flight_no, dep_date, carrier_code)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_cargo_revenue AS
    SELECT
      origin,
      dest,
      carrier_code,
      SUM(weight_kg) AS total_weight_kg,
      SUM(rate * weight_kg) AS total_revenue
    FROM vertex_air_cargo_booking
    WHERE status = 'confirmed'
    GROUP BY origin, dest, carrier_code
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_air_cargo_revenue`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_cargo_booking_flight_date`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_cargo_uld_no`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_cargo_awb_no`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_awb_loaded_in_uld`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_cargo_cass_settlement`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_cargo_claim`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_cargo_booking`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_cargo_uld`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_cargo_awb`.execute(db);
}
