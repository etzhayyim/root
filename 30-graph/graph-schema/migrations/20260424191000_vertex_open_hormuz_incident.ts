import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * open-hormuz-incident — Strait of Hormuz incident workflow (ADR-0017 Maritime Cluster).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_hormuz_military_incident (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      incident_id varchar NOT NULL, imo varchar, vessel_name varchar, flag varchar,
      aggressor_party varchar, incident_type varchar NOT NULL,
      lat double precision, lon double precision, narrative varchar,
      casualties int, vessel_seized boolean,
      severity varchar NOT NULL, require_international_notice boolean,
      occurred_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_hormuz_navigational_incident (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      incident_id varchar NOT NULL, imo varchar, vessel_name varchar, flag varchar,
      incident_type varchar NOT NULL, lat double precision, lon double precision,
      narrative varchar, spill_volume_tonnes double precision,
      severity varchar NOT NULL, require_public_notice boolean,
      occurred_at varchar NOT NULL, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_hormuz_incident_vessel (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_hormuz_military_by_severity AS
      SELECT aggressor_party, severity, COUNT(*) AS incident_count,
             BOOL_OR(vessel_seized) AS any_seizure, MAX(occurred_at) AS latest_occurred
      FROM vertex_open_hormuz_military_incident WHERE status='confirmed'
      GROUP BY aggressor_party, severity;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_hormuz_military_by_severity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_hormuz_incident_vessel`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_hormuz_navigational_incident`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_hormuz_military_incident`.execute(db);
}
