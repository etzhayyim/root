import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-lei Phase 1 — GLEIF Legal Entity Identifier (ISO 17442).
 * Entity registry + direct/ultimate parent ownership graph.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_lei_entity (
      vertex_id      varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      lei            varchar NOT NULL,
      legal_name     varchar NOT NULL,
      country        varchar,
      legal_form     varchar,
      registration_authority varchar,
      registration_status varchar NOT NULL,
      issued_at      varchar,
      next_renewal_at varchar,
      status         varchar NOT NULL,
      created_at     varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_lei_ownership (
      vertex_id      varchar PRIMARY KEY,
      _seq           bigint, created_date date, sensitivity_ord int, owner_did varchar,
      parent_lei     varchar NOT NULL,
      child_lei      varchar NOT NULL,
      relationship_type varchar NOT NULL,
      ownership_pct  double precision,
      relationship_period_start varchar,
      relationship_period_end varchar,
      confidence     double precision,
      source         varchar,
      status         varchar NOT NULL,
      created_at     varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_lei_ownership_pair (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar
    )
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_lei_active_by_country AS
    SELECT country, registration_status,
           COUNT(*) AS entity_count,
           MAX(issued_at) AS latest_issued_at
    FROM vertex_open_lei_entity
    WHERE status='active'
    GROUP BY country, registration_status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_lei_active_by_country`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_lei_ownership_pair`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_lei_ownership`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_lei_entity`.execute(db);
}
