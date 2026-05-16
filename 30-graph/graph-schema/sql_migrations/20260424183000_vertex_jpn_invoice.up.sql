CREATE TABLE vertex_jpn_invoice_issuer (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      registration_number varchar NOT NULL, name_ja varchar NOT NULL,
      issuer_type varchar NOT NULL, corporate_number varchar,
      registered_address varchar, registration_date varchar NOT NULL,
      deregistration_date varchar, status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE vertex_jpn_invoice_corporate_tax (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      filer_corporate_number varchar NOT NULL, fiscal_year varchar NOT NULL,
      taxable_income double precision NOT NULL, tax_payable double precision NOT NULL,
      filing_type varchar NOT NULL, filed_at varchar NOT NULL,
      size_tier varchar NOT NULL, require_audit boolean,
      status varchar NOT NULL, created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE edge_jpn_invoice_filer_issuer (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW mv_jpn_invoice_tax_by_tier AS
      SELECT size_tier, fiscal_year, COUNT(*) AS filing_count,
             SUM(tax_payable) AS total_tax_payable, MAX(filed_at) AS latest_filed
      FROM vertex_jpn_invoice_corporate_tax WHERE status='accepted'
      GROUP BY size_tier, fiscal_year;
