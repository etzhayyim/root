import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-network Phase 1 schema (ADR-0056 BPMN-as-actor).
 *
 *   vertex_open_network_site    — PoP / DC / cell tower / customer edge
 *   vertex_open_network_link    — bidirectional link between two sites
 *   vertex_open_network_change  — change request w/ risk
 *   edge_open_network_link_endpoint
 *   mv_open_network_pending_changes
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_network_site (
      vertex_id       varchar PRIMARY KEY,
      _seq            bigint,
      created_date    date,
      sensitivity_ord int,
      owner_did       varchar,
      operator_org_id varchar NOT NULL,
      site_type       varchar NOT NULL,
      name            varchar,
      latitude        double precision,
      longitude       double precision,
      status          varchar NOT NULL,
      created_at      varchar,
      org_id          varchar,
      user_id         varchar,
      actor_id        varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_open_network_link (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      operator_org_id    varchar NOT NULL,
      from_vertex_id     varchar NOT NULL,
      to_vertex_id       varchar NOT NULL,
      capacity_mbps      double precision NOT NULL,
      media              varchar NOT NULL,
      installed_at       varchar,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_open_network_change (
      vertex_id              varchar PRIMARY KEY,
      _seq                   bigint,
      created_date           date,
      sensitivity_ord        int,
      owner_did              varchar,
      operator_org_id        varchar NOT NULL,
      target_vertex_id       varchar NOT NULL,
      change_type            varchar NOT NULL,
      narrative              varchar,
      affected_customers     int,
      risk                   varchar NOT NULL,
      require_cab_approval   boolean,
      status                 varchar NOT NULL,
      requested_at           varchar NOT NULL,
      approved_at            varchar,
      implemented_at         varchar,
      created_at             varchar,
      org_id                 varchar,
      user_id                varchar,
      actor_id               varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE edge_open_network_link_endpoint (
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
    CREATE MATERIALIZED VIEW mv_open_network_pending_changes AS
    SELECT
      target_vertex_id,
      COUNT(*)                     AS pending_change_count,
      MAX(risk)                    AS worst_risk,
      BOOL_OR(require_cab_approval) AS any_cab_approval,
      MAX(requested_at)            AS latest_requested_at
    FROM vertex_open_network_change
    WHERE status IN ('requested', 'approved')
    GROUP BY target_vertex_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_network_pending_changes`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_network_link_endpoint`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_network_change`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_network_link`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_network_site`.execute(db);
}
