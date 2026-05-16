import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2604291500 JP Corporate Financial Disclosure Ingest.
// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_corp_disclosure (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      jcn VARCHAR,
      edinet_code VARCHAR,
      company_name VARCHAR,
      fiscal_year BIGINT,
      period_start VARCHAR,
      period_end VARCHAR,
      disclosure_kind VARCHAR NOT NULL,
      statement_scope VARCHAR NOT NULL,
      source_id VARCHAR NOT NULL,
      source_record_id VARCHAR NOT NULL,
      source_url VARCHAR,
      artifact_uri VARCHAR,
      source_published_at VARCHAR,
      observed_at VARCHAR,
      extraction_status VARCHAR NOT NULL,
      confidence DOUBLE PRECISION,
      status VARCHAR NOT NULL DEFAULT 'active',

      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      created_at TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_jp_corp_disclosure_jcn
      ON vertex_jp_corp_disclosure (jcn)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_jp_corp_disclosure_edinet
      ON vertex_jp_corp_disclosure (edinet_code)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_jp_corp_disclosure_source
      ON vertex_jp_corp_disclosure (source_id, source_record_id)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_corp_financial_fact (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      disclosure_vid VARCHAR NOT NULL,
      jcn VARCHAR,
      edinet_code VARCHAR,
      fiscal_year BIGINT,
      period_end VARCHAR,
      statement_type VARCHAR NOT NULL,
      concept VARCHAR NOT NULL,
      label_ja VARCHAR,
      value_jpy DOUBLE PRECISION,
      value_text VARCHAR,
      unit VARCHAR,
      source_location VARCHAR NOT NULL,
      extraction_method VARCHAR NOT NULL,
      confidence DOUBLE PRECISION,

      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      created_at TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_jp_corp_fact_disclosure
      ON vertex_jp_corp_financial_fact (disclosure_vid)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_jp_corp_fact_jcn_period
      ON vertex_jp_corp_financial_fact (jcn, period_end)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_corp_finance_coverage (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      jcn VARCHAR NOT NULL,
      company_name VARCHAR,
      disclosure_method VARCHAR,
      latest_period_end VARCHAR,
      latest_disclosure_vid VARCHAR,
      coverage_status VARCHAR NOT NULL,
      missing_reason VARCHAR,
      checked_at VARCHAR NOT NULL,

      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      created_at TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_jp_corp_coverage_jcn
      ON vertex_jp_corp_finance_coverage (jcn)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_corp_finance_coverage_status AS
      SELECT coverage_status, missing_reason, COUNT(*) AS company_count,
             MAX(checked_at) AS latest_checked_at
      FROM vertex_jp_corp_finance_coverage
      GROUP BY coverage_status, missing_reason
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_corp_finance_coverage_status`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_corp_finance_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_corp_financial_fact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_corp_disclosure`.execute(db);
}
