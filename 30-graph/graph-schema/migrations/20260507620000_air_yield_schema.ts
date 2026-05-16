import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_yield_fare_class (
      vertex_id VARCHAR PRIMARY KEY,
      flight_no VARCHAR,
      carrier_code VARCHAR,
      dep_date VARCHAR,
      cabin VARCHAR,
      class_code VARCHAR,
      fare_class VARCHAR,
      seats_available BIGINT,
      inventory BIGINT,
      inventory_delta BIGINT,
      protection_level BIGINT,
      bid_price DOUBLE PRECISION,
      base_fare DOUBLE PRECISION,
      currency VARCHAR,
      adjust_reason VARCHAR,
      fare_code VARCHAR,
      origin_iata VARCHAR,
      dest_iata VARCHAR,
      amount DOUBLE PRECISION,
      effective_date VARCHAR,
      discount_code VARCHAR,
      overbooking_factor DOUBLE PRECISION,
      max_overbooking BIGINT,
      group_ref VARCHAR,
      pax_count BIGINT,
      group_fare DOUBLE PRECISION,
      load_factor DOUBLE PRECISION,
      recommended_fare DOUBLE PRECISION,
      pax_revenue DOUBLE PRECISION,
      cargo_revenue DOUBLE PRECISION,
      ancillary_revenue DOUBLE PRECISION,
      total_revenue DOUBLE PRECISION,
      forecast_pax BIGINT,
      forecast_revenue DOUBLE PRECISION,
      model_version VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_yield_control (
      vertex_id VARCHAR PRIMARY KEY,
      flight_no VARCHAR,
      carrier_code VARCHAR,
      dep_date VARCHAR,
      origin VARCHAR,
      dest VARCHAR,
      load_factor DOUBLE PRECISION,
      bid_price DOUBLE PRECISION,
      revenue DOUBLE PRECISION,
      pax_booked BIGINT,
      capacity BIGINT,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_yield_atpco_fare (
      vertex_id VARCHAR PRIMARY KEY,
      fare_basis VARCHAR,
      origin VARCHAR,
      dest VARCHAR,
      carrier_code VARCHAR,
      amount DOUBLE PRECISION,
      currency VARCHAR,
      cabin VARCHAR,
      rule_no VARCHAR,
      effective_date VARCHAR,
      discontinue_date VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_yield_demand_forecast (
      vertex_id VARCHAR PRIMARY KEY,
      flight_no VARCHAR,
      carrier_code VARCHAR,
      dep_date VARCHAR,
      forecast_pax BIGINT,
      confidence DOUBLE PRECISION,
      model_version VARCHAR,
      forecast_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_air_fare_class_references_atpco (
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
    CREATE INDEX IF NOT EXISTS idx_air_yield_fare_class_flight
      ON vertex_air_yield_fare_class (carrier_code, flight_no, dep_date, class_code)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_yield_atpco_fare_route
      ON vertex_air_yield_atpco_fare (origin, dest, carrier_code, fare_basis)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_revenue_by_route AS
    SELECT
      origin,
      dest,
      carrier_code,
      AVG(load_factor) AS avg_lf,
      SUM(revenue) AS total_revenue
    FROM vertex_air_yield_control
    GROUP BY origin, dest, carrier_code
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_air_revenue_by_route`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_yield_atpco_fare_route`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_yield_fare_class_flight`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_fare_class_references_atpco`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_yield_demand_forecast`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_yield_atpco_fare`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_yield_control`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_yield_fare_class`.execute(db);
}
