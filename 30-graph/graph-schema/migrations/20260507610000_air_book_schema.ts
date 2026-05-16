import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_book_pnr (
      vertex_id VARCHAR PRIMARY KEY,
      pnr_id VARCHAR,
      pnr_ref VARCHAR,
      status VARCHAR,
      booking_source VARCHAR,
      origin VARCHAR,
      dest VARCHAR,
      origin_iata VARCHAR,
      dest_iata VARCHAR,
      dep_date VARCHAR,
      pax_count BIGINT,
      passenger_hash VARCHAR,
      contact_hash VARCHAR,
      total_fare DOUBLE PRECISION,
      refund_amount DOUBLE PRECISION,
      currency VARCHAR,
      carrier_code VARCHAR,
      flight_no VARCHAR,
      payment_ref VARCHAR,
      fare_class VARCHAR,
      cabin_class VARCHAR,
      seat_number VARCHAR,
      seat_class VARCHAR,
      ticket_type VARCHAR,
      cancel_reason VARCHAR,
      cancelled_at VARCHAR,
      original_pnr_ref VARCHAR,
      irrop_reason VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_book_ticket (
      vertex_id VARCHAR PRIMARY KEY,
      ticket_no VARCHAR,
      ticket_number VARCHAR,
      pnr_id VARCHAR,
      pnr_ref VARCHAR,
      passenger_name_hash VARCHAR,
      seat_no VARCHAR,
      fare_basis VARCHAR,
      fare_class VARCHAR,
      issuing_airline VARCHAR,
      status VARCHAR,
      issued_at VARCHAR,
      expires_at VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_book_ancillary (
      vertex_id VARCHAR PRIMARY KEY,
      pnr_id VARCHAR,
      pnr_ref VARCHAR,
      ancillary_type VARCHAR,
      ancillary_code VARCHAR,
      description VARCHAR,
      amount DOUBLE PRECISION,
      quantity BIGINT,
      price DOUBLE PRECISION,
      currency VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_book_bsp_settlement (
      vertex_id VARCHAR PRIMARY KEY,
      settlement_ref VARCHAR,
      period VARCHAR,
      settlement_period VARCHAR,
      carrier_code VARCHAR,
      agent_code VARCHAR,
      ticket_count BIGINT,
      total_amount DOUBLE PRECISION,
      gross_amount DOUBLE PRECISION,
      net_amount DOUBLE PRECISION,
      currency VARCHAR,
      status VARCHAR,
      settled_at VARCHAR,
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
    CREATE TABLE IF NOT EXISTS edge_air_pnr_has_ticket (
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
    CREATE TABLE IF NOT EXISTS edge_air_pnr_has_ancillary (
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
    CREATE INDEX IF NOT EXISTS idx_air_book_pnr_id
      ON vertex_air_book_pnr (pnr_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_book_ticket_no
      ON vertex_air_book_ticket (ticket_no)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_book_pnr_carrier_dep
      ON vertex_air_book_pnr (carrier_code, dep_date)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_booking_by_route AS
    SELECT
      origin,
      dest,
      carrier_code,
      COUNT(*) AS booking_count,
      SUM(total_fare) AS total_revenue
    FROM vertex_air_book_pnr
    WHERE status = 'confirmed' OR status = 'ticketed'
    GROUP BY origin, dest, carrier_code
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_air_booking_by_route`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_book_pnr_carrier_dep`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_book_ticket_no`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_book_pnr_id`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_pnr_has_ancillary`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_pnr_has_ticket`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_book_bsp_settlement`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_book_ancillary`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_book_ticket`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_book_pnr`.execute(db);
}
