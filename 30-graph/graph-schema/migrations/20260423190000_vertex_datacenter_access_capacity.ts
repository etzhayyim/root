import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * ADR-0055 — datacenter access + capacity schema extension.
 *
 * Adds:
 *   vertex_datacenter_access_request        — Tier 1 access request metadata
 *   vertex_datacenter_access_request_pii    — Tier 3 visitor / badge / employer payloads
 *   vertex_datacenter_capacity_reservation  — Tier 1 rack/power/cooling reservation
 *   mv_datacenter_capacity_reserved         — live reserved capacity by facility
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_datacenter_access_request (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      facility_id           varchar NOT NULL,
      sponsor_did           varchar NOT NULL,
      employer_org_id       varchar NOT NULL,
      purpose               varchar NOT NULL,
      access_scope          varchar NOT NULL,
      escort_required       boolean NOT NULL,
      visit_start           varchar NOT NULL,
      visit_end             varchar NOT NULL,
      status                varchar NOT NULL,
      declaration_hash      varchar NOT NULL,
      badge_id              varchar,
      review_comment        varchar,
      reviewed_at           varchar,
      approved_at           varchar,
      approved_by_did       varchar,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_datacenter_access_request_pii (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      facility_id           varchar NOT NULL,
      visitor_payload       varchar NOT NULL,
      employer_payload      varchar,
      badge_payload         varchar,
      safety_payload        varchar,
      retention_until       varchar NOT NULL,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE vertex_datacenter_capacity_reservation (
      vertex_id             varchar PRIMARY KEY,
      _seq                  bigint,
      created_date          date,
      sensitivity_ord       int,
      owner_did             varchar,
      facility_id           varchar NOT NULL,
      requester_did         varchar NOT NULL,
      reservation_type      varchar NOT NULL,
      rack_units            int,
      power_kw              double precision,
      cooling_kw            double precision,
      reservation_start     varchar NOT NULL,
      reservation_end       varchar NOT NULL,
      status                varchar NOT NULL,
      approved_at           varchar,
      approved_by_did       varchar,
      created_at            varchar,
      org_id                varchar,
      user_id               varchar,
      actor_id              varchar
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW mv_datacenter_capacity_reserved AS
    SELECT
      facility_id,
      COALESCE(SUM(rack_units), 0)    AS reserved_rack_units,
      COALESCE(SUM(power_kw), 0)      AS reserved_power_kw,
      COALESCE(SUM(cooling_kw), 0)    AS reserved_cooling_kw
    FROM vertex_datacenter_capacity_reservation
    WHERE status = 'approved'
    GROUP BY facility_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_datacenter_capacity_reserved`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_datacenter_capacity_reservation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_datacenter_access_request_pii`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_datacenter_access_request`.execute(db);
}
