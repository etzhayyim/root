import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * open-opec — Hormuz cluster dependency actor (ADR-0017 Maritime+Energy).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_open_opec_quota_decision (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      meeting_id varchar NOT NULL, meeting_date varchar NOT NULL,
      member_country varchar NOT NULL, quota_mbd double precision NOT NULL,
      quota_mbd_delta double precision, effective_from varchar NOT NULL,
      effective_until varchar, decision_type varchar NOT NULL,
      impact_tier varchar NOT NULL, require_market_notice boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_open_opec_compliance_report (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      report_id varchar NOT NULL, member_country varchar NOT NULL,
      period_month varchar NOT NULL, quota_mbd double precision NOT NULL,
      actual_mbd double precision NOT NULL, compliance_pct double precision NOT NULL,
      reliability_tier varchar NOT NULL, reported_at varchar NOT NULL,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_open_opec_quota_member (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_open_opec_member_compliance AS
      SELECT member_country, reliability_tier, COUNT(*) AS report_count,
             AVG(compliance_pct) AS avg_compliance, MAX(reported_at) AS latest_reported
      FROM vertex_open_opec_compliance_report WHERE status='published'
      GROUP BY member_country, reliability_tier;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_open_opec_member_compliance`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_open_opec_quota_member`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_opec_compliance_report`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_opec_quota_decision`.execute(db);
}
