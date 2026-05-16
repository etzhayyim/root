import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_air_dcs_checkin (
      vertex_id VARCHAR PRIMARY KEY,
      pnr_id_hash VARCHAR,
      pnr_hash VARCHAR,
      flight_no VARCHAR,
      dep_date VARCHAR,
      seat_no VARCHAR,
      seat_number VARCHAR,
      doc_hash VARCHAR,
      gate_code VARCHAR,
      boarding_group VARCHAR,
      dest_country VARCHAR,
      pax_count BIGINT,
      transmission_ref VARCHAR,
      arrival_time VARCHAR,
      gate_ready_time VARCHAR,
      boarding_start_time VARCHAR,
      estimated_dep_time VARCHAR,
      final_pax_count BIGINT,
      boarded_count BIGINT,
      actual_dep_time VARCHAR,
      status VARCHAR,
      channel VARCHAR,
      checkin_at VARCHAR,
      checked_in_at VARCHAR,
      transmitted_at VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_dcs_baggage (
      vertex_id VARCHAR PRIMARY KEY,
      tag_no VARCHAR,
      tag_number VARCHAR,
      pnr_id_hash VARCHAR,
      pnr_hash VARCHAR,
      flight_no VARCHAR,
      dep_date VARCHAR,
      weight_kg DOUBLE PRECISION,
      bag_count BIGINT,
      loaded_count BIGINT,
      offloaded_count BIGINT,
      missing_count BIGINT,
      destination VARCHAR,
      status VARCHAR,
      last_seen_at VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_dcs_load_sheet (
      vertex_id VARCHAR PRIMARY KEY,
      flight_no VARCHAR,
      dep_date VARCHAR,
      total_pax BIGINT,
      pax_count BIGINT,
      bag_weight_kg DOUBLE PRECISION,
      total_cargo_kg DOUBLE PRECISION,
      cargo_weight_kg DOUBLE PRECISION,
      fuel_kg DOUBLE PRECISION,
      zfw_kg DOUBLE PRECISION,
      tow_kg DOUBLE PRECISION,
      lmc_status VARCHAR,
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
    CREATE TABLE IF NOT EXISTS vertex_air_dcs_departure (
      vertex_id VARCHAR PRIMARY KEY,
      flight_no VARCHAR,
      dep_date VARCHAR,
      atd VARCHAR,
      status VARCHAR,
      delay_reason VARCHAR,
      delay_mins BIGINT,
      gate VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_air_checkin_has_baggage (
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
    CREATE TABLE IF NOT EXISTS edge_air_departure_uses_load_sheet (
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
    CREATE INDEX IF NOT EXISTS idx_air_dcs_checkin_flight_date
      ON vertex_air_dcs_checkin (flight_no, dep_date)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_dcs_baggage_tag
      ON vertex_air_dcs_baggage (tag_no)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_air_dcs_checkin_pnr_hash
      ON vertex_air_dcs_checkin (pnr_id_hash)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_air_turnaround_kpi AS
    SELECT
      flight_no,
      dep_date,
      COUNT(DISTINCT vertex_id) AS pax_checkin_count
    FROM vertex_air_dcs_checkin
    WHERE status = 'boarded'
    GROUP BY flight_no, dep_date
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_air_turnaround_kpi`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_dcs_checkin_pnr_hash`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_dcs_baggage_tag`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_air_dcs_checkin_flight_date`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_departure_uses_load_sheet`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_air_checkin_has_baggage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_dcs_departure`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_dcs_load_sheet`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_dcs_baggage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_air_dcs_checkin`.execute(db);
}
