import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-navy-advisory — Hormuz cluster dependency actor (ADR-0017 Maritime+Energy).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_navy_advisory_warning (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      warning_id varchar NOT NULL, authority varchar NOT NULL,
      area_code varchar NOT NULL, area_narrative varchar,
      threat_type varchar NOT NULL, narrative varchar,
      effective_from varchar NOT NULL, effective_until varchar,
      severity varchar NOT NULL, require_broadcast boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_navy_advisory_navarea (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      navarea_id varchar NOT NULL, navarea varchar NOT NULL,
      sequence_number varchar NOT NULL, subject varchar,
      message varchar, coordinator_country varchar,
      issued_at varchar NOT NULL, cancel_at varchar,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_navy_advisory_warning_zone (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_navy_advisory_active AS
      SELECT authority, area_code, severity, COUNT(*) AS warning_count,
             BOOL_OR(require_broadcast) AS any_broadcast, MAX(effective_from) AS latest_effective
      FROM vertex_open_navy_advisory_warning WHERE status='active'
      GROUP BY authority, area_code, severity;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_navy_advisory_active`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_navy_advisory_warning_zone`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_navy_advisory_navarea`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_navy_advisory_warning`.execute(db);
}
