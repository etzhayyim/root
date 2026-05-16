import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * open-airplane Phase 1 schema (ADR-0056 BPMN-as-actor).
 *
 *   vertex_open_airplane_airport   — ICAO / IATA, runways
 *   vertex_open_airplane_aircraft  — tail no. / ICAO 24-bit
 *   vertex_open_airplane_flight    — single flight origin→destination
 *   vertex_open_airplane_incident  — safety incident w/ severity
 *   edge_open_airplane_flight_route      — flight → {origin,destination} airport
 *   mv_open_airplane_open_incidents      — open incident summary per aircraft
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_airplane_airport (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      operator_org_id varchar NOT NULL,
      icao            varchar NOT NULL,
      iata            varchar,
      name            varchar,
      latitude        double precision,
      longitude       double precision,
      runways         int,
      status          varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_open_airplane_aircraft (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      operator_org_id varchar NOT NULL,
      tail_number     varchar NOT NULL,
      icao24          varchar,
      type_icao       varchar,
      status          varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_open_airplane_flight (
      vertex_id         varchar PRIMARY KEY,
      _seq              bigint,
      created_date      date,
      sensitivity_ord   int,
      owner_did         varchar,
      operator_org_id   varchar NOT NULL,
      aircraft_vid      varchar NOT NULL,
      origin_vid        varchar NOT NULL,
      destination_vid   varchar NOT NULL,
      flight_number     varchar NOT NULL,
      scheduled_off     varchar NOT NULL,
      scheduled_in      varchar NOT NULL,
      status            varchar NOT NULL,
      created_at        varchar,
      org_id            varchar,
      user_id           varchar,
      actor_id          varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_open_airplane_incident (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      operator_org_id       varchar NOT NULL,
      aircraft_vid          varchar NOT NULL,
      flight_vid            varchar,
      category              varchar NOT NULL,
      narrative             varchar,
      injuries              int,
      severity              varchar NOT NULL,
      require_public_notice boolean,
      status                varchar NOT NULL,
      reported_at           varchar NOT NULL,
      resolved_at           varchar,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_open_airplane_flight_route (
      edge_id         varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      src_vid         varchar NOT NULL,
      dst_vid         varchar NOT NULL,
      role            varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_open_airplane_open_incidents AS
    SELECT
      aircraft_vid,
      COUNT(*)                       AS open_incident_count,
      MAX(severity)                  AS worst_severity,
      BOOL_OR(require_public_notice) AS any_public_notice,
      MAX(reported_at)               AS latest_reported_at
    FROM vertex_open_airplane_incident
    WHERE status = 'open'
    GROUP BY aircraft_vid
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_airplane_open_incidents`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_airplane_flight_route`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_airplane_incident`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_airplane_flight`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_airplane_aircraft`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_airplane_airport`.execute(db);
}
