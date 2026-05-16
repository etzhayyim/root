import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * jpn-jma Phase 1 — 日本行政機関 BPMN-as-actor (ADR-0056 Wave 6).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_jpn_jma_earthquake (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      event_id varchar NOT NULL, origin_time varchar NOT NULL,
      epicenter_lat double precision NOT NULL, epicenter_lon double precision NOT NULL,
      magnitude double precision NOT NULL, depth_km double precision,
      max_intensity varchar NOT NULL, tsunami_possibility varchar,
      severity varchar NOT NULL, require_emergency_notice boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_jpn_jma_weather_warning (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      warning_code varchar NOT NULL, warning_type varchar NOT NULL,
      area_code varchar NOT NULL, area_name varchar,
      effective_from varchar NOT NULL, effective_until varchar,
      priority varchar NOT NULL, require_broadcast boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_jpn_jma_warning_area (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_jpn_jma_active_warnings AS
      SELECT warning_type, priority, COUNT(*) AS warning_count,
             BOOL_OR(require_broadcast) AS any_broadcast, MAX(effective_from) AS latest_effective
      FROM vertex_jpn_jma_weather_warning WHERE status='active'
      GROUP BY warning_type, priority;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jpn_jma_active_warnings`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jpn_jma_warning_area`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jpn_jma_weather_warning`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jpn_jma_earthquake`.execute(db);
}
