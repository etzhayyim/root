import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_transit_route (
      vertex_id      varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      agency_org_id  varchar NOT NULL,
      route_code     varchar NOT NULL,
      route_type     varchar NOT NULL,
      name           varchar,
      headsign_fwd   varchar,
      headsign_rev   varchar,
      color          varchar,
      status         varchar NOT NULL,
      created_at     varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_transit_delay (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint, created_date date, sensitivity_ord int, owner_did varchar,
      agency_org_id         varchar NOT NULL,
      route_vertex_id       varchar NOT NULL,
      stop_sequence         int,
      delay_minutes         int NOT NULL,
      reason                varchar,
      severity              varchar NOT NULL,
      require_public_notice boolean,
      status                varchar NOT NULL,
      reported_at           varchar NOT NULL,
      cleared_at            varchar,
      created_at            varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_transit_delay_route (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_transit_active_delays AS
    SELECT route_vertex_id,
           COUNT(*) AS active_delay_count,
           MAX(severity) AS worst_severity,
           BOOL_OR(require_public_notice) AS any_public_notice,
           MAX(delay_minutes) AS max_delay_minutes,
           MAX(reported_at) AS latest_reported_at
    FROM vertex_open_transit_delay WHERE status='active'
    GROUP BY route_vertex_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_transit_active_delays`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_transit_delay_route`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_transit_delay`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_transit_route`.execute(db);
}
