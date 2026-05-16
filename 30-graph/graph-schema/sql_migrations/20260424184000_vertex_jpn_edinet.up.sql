CREATE TABLE vertex_jpn_edinet_securities_filing (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      doc_id varchar NOT NULL, edinet_code varchar NOT NULL, issuer_name varchar,
      doc_type_code varchar NOT NULL, doc_description varchar,
      fiscal_year_end varchar, submitted_at varchar NOT NULL,
      period_covered varchar, disclosure_tier varchar NOT NULL,
      require_market_notice boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_jpn_edinet_material_event (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      event_id varchar NOT NULL, edinet_code varchar NOT NULL, issuer_name varchar,
      event_type varchar NOT NULL, narrative varchar,
      occurred_at varchar NOT NULL, reported_at varchar NOT NULL,
      priority varchar NOT NULL, require_trading_halt boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_jpn_edinet_event_filing (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_jpn_edinet_filings_by_issuer AS
      SELECT edinet_code, doc_type_code, COUNT(*) AS filing_count,
             MAX(submitted_at) AS latest_submitted_at
      FROM vertex_jpn_edinet_securities_filing WHERE status='published'
      GROUP BY edinet_code, doc_type_code;
