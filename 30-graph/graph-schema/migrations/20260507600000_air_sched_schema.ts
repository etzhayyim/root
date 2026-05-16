import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_sched_schedule (
      vertex_id VARCHAR PRIMARY KEY,
      flight_no VARCHAR,
      carrier_code VARCHAR,
      origin VARCHAR,
      dest VARCHAR,
      dep_date VARCHAR,
      dep_iata VARCHAR,
      arr_iata VARCHAR,
      dep_time VARCHAR,
      arr_time VARCHAR,
      aircraft_type VARCHAR,
      tail_number VARCHAR,
      effective_date VARCHAR,
      end_date VARCHAR,
      season_code VARCHAR,
      valid_from VARCHAR,
      valid_to VARCHAR,
      season VARCHAR,
      frequency_days VARCHAR,
      old_frequency VARCHAR,
      new_frequency VARCHAR,
      flight_count BIGINT,
      published_at VARCHAR,
      gate_code VARCHAR,
      terminal VARCHAR,
      airport VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_sched_slot (
      vertex_id VARCHAR PRIMARY KEY,
      airport VARCHAR,
      slot_ref VARCHAR,
      slot_date VARCHAR,
      slot_time VARCHAR,
      dep_date VARCHAR,
      dep_iata VARCHAR,
      slot_type VARCHAR,
      requested_time VARCHAR,
      allocated_time VARCHAR,
      allocated_by VARCHAR,
      movement_type VARCHAR,
      carrier_code VARCHAR,
      flight_no VARCHAR,
      status VARCHAR,
      coordinator VARCHAR,
      season VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_sched_route (
      vertex_id VARCHAR PRIMARY KEY,
      origin VARCHAR,
      dest VARCHAR,
      distance_nm BIGINT,
      route_type VARCHAR,
      restriction VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_sched_codeshare (
      vertex_id VARCHAR PRIMARY KEY,
      operating_carrier VARCHAR,
      marketing_carrier VARCHAR,
      operating_flight_no VARCHAR,
      marketing_flight_no VARCHAR,
      partner_airline VARCHAR,
      dep_date VARCHAR,
      seat_allocation BIGINT,
      effective_date VARCHAR,
      end_date VARCHAR,
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
    CREATE TABLE IF NOT EXISTS edge_air_schedule_uses_route (
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
    CREATE TABLE IF NOT EXISTS edge_air_schedule_has_slot (
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
    CREATE INDEX IF NOT EXISTS idx_air_sched_schedule_carrier_flight
      ON vertex_air_sched_schedule (carrier_code, flight_no)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_sched_schedule_origin_dest
      ON vertex_air_sched_schedule (origin, dest)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_sched_slot_airport_date
      ON vertex_air_sched_slot (airport, slot_date)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_schedule_daily AS
    SELECT
      origin,
      dest,
      carrier_code,
      COUNT(*) AS flight_count,
      MIN(dep_time) AS first_dep,
      MAX(arr_time) AS last_arr
    FROM vertex_air_sched_schedule
    WHERE status = 'active'
    GROUP BY origin, dest, carrier_code
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_air_schedule_daily`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_sched_slot_airport_date`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_sched_schedule_origin_dest`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_sched_schedule_carrier_flight`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_schedule_has_slot`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_schedule_uses_route`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_sched_codeshare`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_sched_route`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_sched_slot`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_sched_schedule`.execute(db);
}
