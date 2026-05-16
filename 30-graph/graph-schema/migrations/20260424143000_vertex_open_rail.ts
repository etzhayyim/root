import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_rail_line (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      operator_org_id varchar NOT NULL, line_code varchar NOT NULL, name varchar,
      gauge_mm int, length_km double precision,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_rail_station (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      operator_org_id varchar NOT NULL, line_vid varchar NOT NULL, station_code varchar NOT NULL,
      name varchar, km_post double precision, stop_order int,
      latitude double precision, longitude double precision,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_rail_incident (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      operator_org_id varchar NOT NULL, line_vid varchar NOT NULL, run_vid varchar,
      category varchar NOT NULL, narrative varchar, delay_minutes int,
      severity varchar NOT NULL, require_public_notice boolean,
      status varchar NOT NULL, reported_at varchar NOT NULL, resolved_at varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_rail_line_station (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, stop_order int NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_rail_open_incidents AS
    SELECT line_vid, COUNT(*) AS open_incident_count, MAX(severity) AS worst_severity,
           BOOL_OR(require_public_notice) AS any_public_notice,
           SUM(delay_minutes) AS total_delay_minutes, MAX(reported_at) AS latest_reported_at
    FROM vertex_open_rail_incident WHERE status='open' GROUP BY line_vid
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_rail_open_incidents`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_rail_line_station`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_rail_incident`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_rail_station`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_rail_line`.execute(db);
}
