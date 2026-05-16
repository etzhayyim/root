import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * jpn-edinet Phase 1 — 日本行政機関 BPMN-as-actor (ADR-0056 Wave 6).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE vertex_jpn_edinet_securities_filing (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      doc_id varchar NOT NULL, edinet_code varchar NOT NULL, issuer_name varchar,
      doc_type_code varchar NOT NULL, doc_description varchar,
      fiscal_year_end varchar, submitted_at varchar NOT NULL,
      period_covered varchar, disclosure_tier varchar NOT NULL,
      require_market_notice boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE vertex_jpn_edinet_material_event (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      event_id varchar NOT NULL, edinet_code varchar NOT NULL, issuer_name varchar,
      event_type varchar NOT NULL, narrative varchar,
      occurred_at varchar NOT NULL, reported_at varchar NOT NULL,
      priority varchar NOT NULL, require_trading_halt boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE TABLE edge_jpn_edinet_event_filing (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar)
  `.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_jpn_edinet_filings_by_issuer AS
      SELECT edinet_code, doc_type_code, COUNT(*) AS filing_count,
             MAX(submitted_at) AS latest_submitted_at
      FROM vertex_jpn_edinet_securities_filing WHERE status='published'
      GROUP BY edinet_code, doc_type_code;
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jpn_edinet_filings_by_issuer`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jpn_edinet_event_filing`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jpn_edinet_material_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jpn_edinet_securities_filing`.execute(db);
}
