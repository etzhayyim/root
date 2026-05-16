CREATE TABLE IF NOT EXISTS vertex_public_statement (
      vertex_id           VARCHAR PRIMARY KEY,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      rkey                VARCHAR,
      repo                VARCHAR,
      label               VARCHAR,
      statement_type      VARCHAR,
      title               VARCHAR,
      publisher           VARCHAR,
      published_at        VARCHAR,
      language            VARCHAR,
      source_url          VARCHAR,
      source_domain       VARCHAR,
      source_license      VARCHAR,
      summary             VARCHAR,
      props               VARCHAR,
      ingested_at         VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_legal_entity_mentions (
      edge_id             VARCHAR PRIMARY KEY,
      src_vid             VARCHAR,
      dst_vid             VARCHAR,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      role                VARCHAR,
      mention_text        VARCHAR,
      source_statement_vid VARCHAR,
      source_url          VARCHAR,
      source_license      VARCHAR,
      confidence          DOUBLE PRECISION,
      linked_at           VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_legal_entity_relates_to (
      edge_id             VARCHAR PRIMARY KEY,
      src_vid             VARCHAR,
      dst_vid             VARCHAR,
      _seq                BIGINT,
      created_date        DATE,
      sensitivity_ord     BIGINT,
      owner_did           VARCHAR,
      relationship_type   VARCHAR,
      relation_scope      VARCHAR,
      amount              DOUBLE PRECISION,
      amount_currency     VARCHAR,
      period_start        VARCHAR,
      period_end          VARCHAR,
      source_statement_vid VARCHAR,
      source_url          VARCHAR,
      source_license      VARCHAR,
      confidence          DOUBLE PRECISION,
      linked_at           VARCHAR
    );

DROP MATERIALIZED VIEW IF EXISTS mv_legal_entity_disclosure_coverage;

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
    ),
    relationship_rollup AS (
      SELECT
        src_vid AS company_did,
        COUNT(*) AS relationship_edge_count
      FROM edge_legal_entity_relates_to
      WHERE src_vid IS NOT NULL
      GROUP BY src_vid
    ),
    statement_rollup AS (
      SELECT
        em.dst_vid AS company_did,
        COUNT(DISTINCT em.source_statement_vid) AS statement_count
      FROM edge_legal_entity_mentions em
      WHERE em.dst_vid IS NOT NULL
        AND em.source_statement_vid IS NOT NULL
      GROUP BY em.dst_vid
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
      COALESCE(rr.relationship_edge_count, 0) AS relationship_edge_count,
      COALESCE(sr.statement_count, 0) AS statement_count,
      COALESCE(fc.last_filing_seq, 0) AS last_filing_seq,
      (
        COALESCE(CASE WHEN fc.filings_count > 0 THEN 1 ELSE 0 END, 0) +
        COALESCE(CASE WHEN fr.has_revenue_fact > 0 THEN 1 ELSE 0 END, 0) +
        COALESCE(CASE WHEN fr.has_employee_fact > 0 THEN 1 ELSE 0 END, 0) +
        COALESCE(CASE WHEN or1.subsidiaries_count > 0 THEN 1 ELSE 0 END, 0) +
        COALESCE(CASE WHEN (tr.trade_edge_count + rr.relationship_edge_count) > 0 THEN 1 ELSE 0 END, 0) +
        COALESCE(CASE WHEN sr.statement_count > 0 THEN 1 ELSE 0 END, 0)
      )::DOUBLE PRECISION / 6.0 AS disclosure_coverage_score
    FROM vertex_legal_entity le
    LEFT JOIN filing_counts fc ON fc.company_did = le.vertex_id
    LEFT JOIN fact_rollup fr ON fr.company_did = le.vertex_id
    LEFT JOIN ownership_rollup or1 ON or1.company_did = le.vertex_id
    LEFT JOIN trade_rollup tr ON tr.company_did = le.vertex_id
    LEFT JOIN relationship_rollup rr ON rr.company_did = le.vertex_id
    LEFT JOIN statement_rollup sr ON sr.company_did = le.vertex_id;
