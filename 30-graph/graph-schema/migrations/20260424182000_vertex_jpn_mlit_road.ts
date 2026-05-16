import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * jpn-mlit-road Phase 1 — 日本行政機関 BPMN-as-actor (ADR-0056 Wave 6).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_jpn_mlit_road_construction (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      construction_id varchar NOT NULL, road_code varchar NOT NULL,
      section_from varchar, section_to varchar,
      work_type varchar NOT NULL, contractor_org_id varchar,
      start_date varchar NOT NULL, end_date varchar NOT NULL,
      expected_impact varchar NOT NULL,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_jpn_mlit_road_restriction (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      restriction_id varchar NOT NULL, road_code varchar NOT NULL,
      restriction_type varchar NOT NULL, reason varchar,
      section_from varchar, section_to varchar,
      effective_from varchar NOT NULL, effective_until varchar,
      severity varchar NOT NULL, require_public_notice boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_jpn_mlit_road_work_road (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_jpn_mlit_active_restrictions AS
      SELECT road_code, restriction_type, COUNT(*) AS restriction_count,
             BOOL_OR(require_public_notice) AS any_public_notice, MAX(effective_from) AS latest_effective
      FROM vertex_jpn_mlit_road_restriction WHERE status='active'
      GROUP BY road_code, restriction_type;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jpn_mlit_active_restrictions`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jpn_mlit_road_work_road`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jpn_mlit_road_restriction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jpn_mlit_road_construction`.execute(db);
}
