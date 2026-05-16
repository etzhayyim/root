import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-gulf-terminal — Hormuz cluster dependency actor (ADR-0017 Maritime+Energy).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_gulf_terminal_loading (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      loading_id varchar NOT NULL, terminal_code varchar NOT NULL,
      terminal_name varchar, country varchar NOT NULL,
      imo varchar NOT NULL, vessel_name varchar,
      crude_grade varchar NOT NULL, volume_tonnes double precision NOT NULL,
      quota_ref varchar, bl_date varchar NOT NULL, departed_at varchar,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_gulf_terminal_outage (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      outage_id varchar NOT NULL, terminal_code varchar NOT NULL,
      cause varchar NOT NULL, impact_mbd double precision,
      narrative varchar, expected_duration_hours double precision,
      severity varchar NOT NULL, require_market_notice boolean,
      started_at varchar NOT NULL, resolved_at varchar,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_gulf_terminal_loading_vessel (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_gulf_terminal_throughput AS
      SELECT terminal_code, crude_grade, COUNT(*) AS loading_count,
             SUM(volume_tonnes) AS total_tonnes, MAX(bl_date) AS latest_bl
      FROM vertex_open_gulf_terminal_loading WHERE status='completed'
      GROUP BY terminal_code, crude_grade;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_gulf_terminal_throughput`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_gulf_terminal_loading_vessel`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_gulf_terminal_outage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_gulf_terminal_loading`.execute(db);
}
