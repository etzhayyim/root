import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_road_road (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint, created_date date, sensitivity_ord int, owner_did varchar,
      authority_org_id varchar NOT NULL,
      road_code        varchar NOT NULL,
      name             varchar,
      road_class       varchar NOT NULL,
      length_km        double precision,
      jurisdiction     varchar,
      lane_count       int,
      status           varchar NOT NULL,
      created_at       varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_road_incident (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint, created_date date, sensitivity_ord int, owner_did varchar,
      authority_org_id      varchar NOT NULL,
      road_vertex_id        varchar NOT NULL,
      category              varchar NOT NULL,
      narrative             varchar,
      injuries              int,
      affected_lane_count   int,
      estimated_delay_minutes int,
      severity              varchar NOT NULL,
      require_public_notice boolean,
      status                varchar NOT NULL,
      reported_at           varchar NOT NULL,
      resolved_at           varchar,
      created_at            varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_road_incident_road (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_road_open_incidents AS
    SELECT road_vertex_id,
           COUNT(*) AS open_incident_count,
           MAX(severity) AS worst_severity,
           BOOL_OR(require_public_notice) AS any_public_notice,
           SUM(estimated_delay_minutes) AS total_delay_minutes,
           MAX(reported_at) AS latest_reported_at
    FROM vertex_open_road_incident WHERE status='open'
    GROUP BY road_vertex_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_road_open_incidents`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_road_incident_road`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_road_incident`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_road_road`.execute(db);
}
