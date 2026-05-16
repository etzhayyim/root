CREATE TABLE IF NOT EXISTS vertex_isin_security (
      vertex_id         VARCHAR PRIMARY KEY,
      isin              VARCHAR,
      ticker            VARCHAR,
      cik               VARCHAR,
      figi              VARCHAR,
      composite_figi    VARCHAR,
      share_class_figi  VARCHAR,
      company_name      VARCHAR,
      exchange_code     VARCHAR,
      exchange_mic      VARCHAR,
      market_sector     VARCHAR,
      security_type     VARCHAR,
      security_type2    VARCHAR,
      currency          VARCHAR,
      country_iso2      VARCHAR,
      sic               VARCHAR,
      sic_desc          VARCHAR,
      edinet_code       VARCHAR,
      status            VARCHAR NOT NULL DEFAULT 'active',
      actor_did         VARCHAR NOT NULL,
      org_did           VARCHAR NOT NULL,
      created_at        TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_isin_security_isin
      ON vertex_isin_security (isin);

CREATE INDEX IF NOT EXISTS idx_isin_security_ticker
      ON vertex_isin_security (ticker);

CREATE INDEX IF NOT EXISTS idx_isin_security_cik
      ON vertex_isin_security (cik);

CREATE TABLE IF NOT EXISTS vertex_isin_filing (
      vertex_id         VARCHAR PRIMARY KEY,
      ticker            VARCHAR,
      edinet_code       VARCHAR,
      doc_id            VARCHAR,
      doc_type          VARCHAR,
      doc_type_code     VARCHAR,
      period_start      VARCHAR,
      period_end        VARCHAR,
      filing_date       VARCHAR,
      company_name      VARCHAR,
      doc_description   VARCHAR,
      pdf_flag          VARCHAR,
      actor_did         VARCHAR NOT NULL,
      org_did           VARCHAR NOT NULL,
      created_at        TIMESTAMP
    );

CREATE INDEX IF NOT EXISTS idx_isin_filing_ticker
      ON vertex_isin_filing (ticker);

CREATE INDEX IF NOT EXISTS idx_isin_filing_edinet_code
      ON vertex_isin_filing (edinet_code);
