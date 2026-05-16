import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-water Phase 1 schema (ADR-0056 BPMN-as-actor pattern).
 *
 *   vertex_open_water_node          — reservoir / pumping-station / service-point
 *   vertex_open_water_main          — pipe segment (node → node)
 *   vertex_open_water_leak          — leak report + severity
 *   edge_open_water_main_endpoint   — main → endpoint node traceability
 *   mv_open_water_open_leaks        — unresolved leaks per main (for dashboards)
 *
 * Mirrors 20260423190000_vertex_open_seiyaku.ts row shape (sensitivity_ord /
 * owner_did / org_id / user_id / actor_id + _seq + created_date) so RLS and
 * graph-worker projection stay uniform.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_water_node (
      vertex_id        varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      utility_org_id   varchar NOT NULL,
      node_type        varchar NOT NULL,
      name             varchar,
      capacity_m3      double precision,
      latitude         double precision,
      longitude        double precision,
      status           varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_open_water_main (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      utility_org_id     varchar NOT NULL,
      from_vertex_id     varchar NOT NULL,
      to_vertex_id       varchar NOT NULL,
      diameter_mm        int NOT NULL,
      material           varchar NOT NULL,
      length_m           double precision NOT NULL,
      installed_at       varchar,
      pressure_zone      varchar,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_open_water_leak (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      utility_org_id         varchar NOT NULL,
      main_vertex_id         varchar NOT NULL,
      latitude               double precision,
      longitude              double precision,
      estimated_flow_lpm     double precision,
      contamination_risk     varchar,
      severity               varchar NOT NULL,
      require_public_notice  boolean,
      status                 varchar NOT NULL,
      reported_at            varchar NOT NULL,
      resolved_at            varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_open_water_main_endpoint (
      edge_id          varchar PRIMARY KEY,
      _seq             bigint,
      created_date     date,
      sensitivity_ord  int,
      owner_did        varchar,
      src_vid          varchar NOT NULL,
      dst_vid          varchar NOT NULL,
      role             varchar NOT NULL,
      created_at       varchar,
      org_id           varchar,
      user_id          varchar,
      actor_id         varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_open_water_open_leaks AS
    SELECT
      main_vertex_id,
      COUNT(*)                              AS open_leak_count,
      MAX(severity)                         AS worst_severity,
      BOOL_OR(require_public_notice)        AS any_public_notice,
      MAX(reported_at)                      AS latest_reported_at
    FROM vertex_open_water_leak
    WHERE status = 'open'
    GROUP BY main_vertex_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_water_open_leaks`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_water_main_endpoint`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_water_leak`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_water_main`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_water_node`.execute(db);
}
