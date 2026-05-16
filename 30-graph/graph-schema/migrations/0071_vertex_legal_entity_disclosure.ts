import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 0071: legal-entity disclosure graph spine.
 *
 * Goal:
 *   Extend LEI / registry-level entity anchors into public-company disclosure data:
 *   filings, extracted facts, ownership/subsidiary links, and customer/supplier links.
 *
 * Scope:
 *   - vertex_company_filing         issuer filing metadata (10-K, 20-F, annual report, etc.)
 *   - vertex_company_fact           extracted numeric/text facts from filings
 *   - edge_legal_entity_owns        parent/subsidiary or control relationships
 *   - edge_legal_entity_trades_with customer/supplier/partner relationships
 *   - mv_legal_entity_disclosure_coverage  per-entity disclosure completeness rollup
 *
 * This intentionally does not overload edge_owned_by, which lacks stake/control
 * semantics needed for corporate ownership graphs.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_company_filing (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      label             VARCHAR,
      company_did       VARCHAR,
      filing_source     VARCHAR,
      filing_type       VARCHAR,
      filing_date       VARCHAR,
      period_start      VARCHAR,
      period_end        VARCHAR,
      fiscal_year       INT,
      fiscal_quarter    INT,
      accession_no      VARCHAR,
      filing_url        VARCHAR,
      issuer_name       VARCHAR,
      issuer_ticker     VARCHAR,
      issuer_exchange   VARCHAR,
      country           VARCHAR,
      language          VARCHAR,
      source_license    VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_company_fact (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      label             VARCHAR,
      company_did       VARCHAR,
      filing_did        VARCHAR,
      fact_namespace    VARCHAR,
      fact_name         VARCHAR,
      fact_value_num    DOUBLE PRECISION,
      fact_value_text   VARCHAR,
      unit              VARCHAR,
      currency          VARCHAR,
      period_start      VARCHAR,
      period_end        VARCHAR,
      as_of_date        VARCHAR,
      fiscal_year       INT,
      fiscal_quarter    INT,
      source_url        VARCHAR,
      source_method     VARCHAR,
      confidence        DOUBLE PRECISION,
      ingested_at       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_legal_entity_owns (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      relationship      VARCHAR,
      stake_pct         DOUBLE PRECISION,
      voting_pct        DOUBLE PRECISION,
      control_type      VARCHAR,
      effective_from    VARCHAR,
      effective_to      VARCHAR,
      source_url        VARCHAR,
      source_license    VARCHAR,
      confidence        DOUBLE PRECISION,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_legal_entity_trades_with (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      relationship      VARCHAR,
      amount            DOUBLE PRECISION,
      amount_currency   VARCHAR,
      period_start      VARCHAR,
      period_end        VARCHAR,
      source_url        VARCHAR,
      source_license    VARCHAR,
      confidence        DOUBLE PRECISION,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_legal_entity_disclosure_coverage AS
    WITH filing_counts AS (
      SELECT
        company_did,
        COUNT(*) AS filings_count,
        MAX(_seq) AS last_filing_seq
      FROM vertex_company_filing
      WHERE company_did IS NOT NULL
      GROUP BY company_did
    ),
    fact_rollup AS (
      SELECT
        company_did,
        COUNT(*) AS fact_count,
        MAX(CASE
          WHEN LOWER(fact_name) IN ('revenue', 'sales', 'net_sales', 'sales_revenue', 'revenue_total')
          THEN 1 ELSE 0
        END) AS has_revenue_fact,
        MAX(CASE
          WHEN LOWER(fact_name) IN ('employee_count', 'employees', 'headcount', 'number_of_employees')
          THEN 1 ELSE 0
        END) AS has_employee_fact
      FROM vertex_company_fact
      WHERE company_did IS NOT NULL
      GROUP BY company_did
    ),
    ownership_rollup AS (
      SELECT
        src_vid AS company_did,
        COUNT(*) AS subsidiaries_count
      FROM edge_legal_entity_owns
      WHERE src_vid IS NOT NULL
      GROUP BY src_vid
    ),
    trade_rollup AS (
      SELECT
        src_vid AS company_did,
        COUNT(*) AS trade_edge_count
      FROM edge_legal_entity_trades_with
      WHERE src_vid IS NOT NULL
      GROUP BY src_vid
    )
    SELECT
      le.vertex_id AS company_did,
      le.name,
      le.country,
      le.jurisdiction,
      le.source,
      COALESCE(fc.filings_count, 0) AS filings_count,
      COALESCE(fr.fact_count, 0) AS fact_count,
      COALESCE(fr.has_revenue_fact, 0) AS has_revenue_fact,
      COALESCE(fr.has_employee_fact, 0) AS has_employee_fact,
      COALESCE(or1.subsidiaries_count, 0) AS subsidiaries_count,
      COALESCE(tr.trade_edge_count, 0) AS trade_edge_count,
      COALESCE(fc.last_filing_seq, 0) AS last_filing_seq,
      (
        COALESCE(CASE WHEN fc.filings_count > 0 THEN 1 ELSE 0 END, 0) +
        COALESCE(CASE WHEN fr.has_revenue_fact > 0 THEN 1 ELSE 0 END, 0) +
        COALESCE(CASE WHEN fr.has_employee_fact > 0 THEN 1 ELSE 0 END, 0) +
        COALESCE(CASE WHEN or1.subsidiaries_count > 0 THEN 1 ELSE 0 END, 0) +
        COALESCE(CASE WHEN tr.trade_edge_count > 0 THEN 1 ELSE 0 END, 0)
      )::DOUBLE PRECISION / 5.0 AS disclosure_coverage_score
    FROM vertex_legal_entity le
    LEFT JOIN filing_counts fc ON fc.company_did = le.vertex_id
    LEFT JOIN fact_rollup fr ON fr.company_did = le.vertex_id
    LEFT JOIN ownership_rollup or1 ON or1.company_did = le.vertex_id
    LEFT JOIN trade_rollup tr ON tr.company_did = le.vertex_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_legal_entity_disclosure_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_legal_entity_trades_with`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_legal_entity_owns`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_company_fact`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_company_filing`.execute(db);
}
