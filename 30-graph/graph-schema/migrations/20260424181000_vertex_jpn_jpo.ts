import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B
// tier: C

/**
 * jpn-jpo Phase 1 — 日本行政機関 BPMN-as-actor (ADR-0056 Wave 6).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_jpn_jpo_application (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      application_number varchar NOT NULL, applicant_did varchar NOT NULL,
      inventor_names varchar, ipc_classes varchar, title varchar,
      filing_date varchar NOT NULL, priority_date varchar,
      examination_requested boolean, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_jpn_jpo_examination (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      application_number varchar NOT NULL, decision varchar NOT NULL,
      decision_date varchar NOT NULL, examiner_id varchar,
      rejection_grounds varchar, cited_art varchar,
      next_action varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_jpn_jpo_app_examination (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_jpn_jpo_app_by_ipc AS
      SELECT ipc_classes, status, COUNT(*) AS app_count, MAX(filing_date) AS latest_filing
      FROM vertex_jpn_jpo_application WHERE status IN ('filed','pending','granted')
      GROUP BY ipc_classes, status;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jpn_jpo_app_by_ipc`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jpn_jpo_app_examination`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jpn_jpo_examination`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jpn_jpo_application`.execute(db);
}
