import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0035 / ADR-0002 — JP fiscal intel graph.
// tier: B for public fiscal vertices and edges; Tier 3 details must stay out of graph.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_source (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      source_id varchar NOT NULL, collection varchar NOT NULL, jurisdiction varchar NOT NULL DEFAULT 'JPN',
      title varchar NOT NULL, publisher_did varchar, source_url varchar NOT NULL, access_kind varchar NOT NULL,
      cadence varchar NOT NULL, license_note varchar, extractor varchar NOT NULL, status varchar NOT NULL,
      notes varchar, created_at timestamptz NOT NULL, updated_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_document (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      source_id varchar NOT NULL, collection varchar NOT NULL, source_url varchar NOT NULL, fetched_at timestamptz,
      media_type varchar, sha256 varchar, byte_length bigint, storage_uri varchar, title varchar,
      text_excerpt varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_budget_book (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      fiscal_year int NOT NULL, doc_type varchar NOT NULL, account_type varchar NOT NULL,
      special_account_code varchar, total_jpy bigint NOT NULL, source_url varchar NOT NULL,
      pdf_cid varchar, xbrl_cid varchar, source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_appropriation (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      fiscal_year int NOT NULL, account_type varchar NOT NULL, special_account_code varchar,
      ministry_did varchar NOT NULL, program_code varchar NOT NULL, program_name varchar,
      amount_jpy bigint NOT NULL, diet_approval_id varchar, doc_type varchar, source_url varchar,
      source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_budget_execution (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      program_code varchar NOT NULL, fiscal_year int NOT NULL, quarter int NOT NULL,
      appropriated_jpy bigint, executed_jpy bigint NOT NULL, remaining_jpy bigint,
      derivation_stage varchar, source_url varchar, source_id varchar, document_id varchar,
      created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_procurement_bid (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      tender_no varchar NOT NULL, issuer_did varchar NOT NULL, method varchar NOT NULL, title varchar,
      estimated_jpy bigint, currency varchar NOT NULL DEFAULT 'JPY', opened_at timestamptz NOT NULL,
      closed_at timestamptz, awarded_at timestamptz, awarded_contract_did varchar, awarded_amount_jpy bigint,
      bidders_json varchar, tender_url varchar, external_refs_json varchar, source_id varchar,
      document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_contract (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      issuer_did varchar NOT NULL, contractor_did varchar NOT NULL, contractor_jcn varchar, contract_no varchar,
      method varchar NOT NULL, amount_jpy bigint NOT NULL, signed_date date NOT NULL, deliverable varchar,
      kaikeiho_article varchar, program_code varchar, tender_did varchar, publication_url varchar,
      supersedes_uri varchar, source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_payment_record (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      contract_did varchar NOT NULL, contract_uri varchar, payee_did varchar NOT NULL, tranches_json varchar,
      paid_jpy bigint NOT NULL, remaining_jpy bigint, fiscal_year int, derivation_stage varchar,
      source_url varchar, source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_subsidy_grant (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      source_did varchar NOT NULL, recipient_did varchar NOT NULL, program varchar NOT NULL, program_code varchar,
      amount_jpy bigint NOT NULL, decision_date date NOT NULL, kofu_yokou varchar, publication_url varchar,
      pii_tier int, source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_tax_payment (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      payer_cohort_did varchar NOT NULL, receiver_did varchar NOT NULL, tax_code varchar NOT NULL,
      amount_jpy bigint NOT NULL, period_iso varchar NOT NULL, pii_tier int, source_url varchar,
      source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_kofuzei_transfer (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      source_ministry_did varchar NOT NULL, recipient_lg_did varchar NOT NULL, basis varchar NOT NULL,
      program_code varchar, amount_jpy bigint NOT NULL, fiscal_year int NOT NULL, derivation_stage varchar,
      source_url varchar, source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_lg_finance (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      team_code varchar NOT NULL, team_name varchar, level varchar, fiscal_year int NOT NULL,
      revenue_jpy bigint NOT NULL, expense_jpy bigint NOT NULL, local_tax_jpy bigint, kofuzei_jpy bigint,
      kokko_shishutsukin_jpy bigint, debt_stock_jpy bigint, generic_ratio double precision,
      source_url varchar, source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_incorp_finance (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      incorp_did varchar NOT NULL, incorp_jcn varchar, incorp_type varchar, fiscal_year int NOT NULL,
      subsidy_from_did varchar, subsidy_jpy bigint, total_revenue_jpy bigint, total_expense_jpy bigint,
      xbrl_cid varchar, source_url varchar, source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_program_review (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      program_code varchar NOT NULL, program_name varchar, ministry_did varchar NOT NULL, fiscal_year int NOT NULL,
      review_rating varchar, recommended_action varchar, spent_jpy bigint, sheet_url varchar, sheet_cid varchar,
      source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_audit_finding (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      target_did varchar NOT NULL, fiscal_year int NOT NULL, category varchar NOT NULL, sub_category varchar,
      amount_jpy bigint, paragraph_ref varchar NOT NULL, summary varchar, source_url varchar,
      source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_beneficial_owner (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      child_did varchar NOT NULL, child_jcn varchar, parent_did varchar NOT NULL, parent_type varchar,
      ownership_pct double precision, voting_pct double precision, evidence_kind varchar NOT NULL,
      evidence_url varchar, observed_at date NOT NULL, status varchar NOT NULL, opacity_reason varchar,
      external_refs_json varchar, pii_tier int, source_id varchar, document_id varchar, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_jp_fiscal_public_statement (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      speaker_did varchar NOT NULL, speaker_name varchar, speaker_role varchar, organization_did varchar,
      statement_kind varchar NOT NULL, stated_at timestamptz, title varchar, text_excerpt varchar,
      source_url varchar NOT NULL, source_id varchar, document_id varchar, topics_json varchar,
      created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jp_fiscal_evidence (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, evidence_kind varchar NOT NULL, source_url varchar,
      confidence double precision, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jp_fiscal_flow (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, flow_type varchar NOT NULL, collection varchar NOT NULL,
      source_did varchar NOT NULL, dest_did varchar NOT NULL, amount_jpy bigint NOT NULL DEFAULT 0,
      fiscal_year int, program_code varchar, contract_ref varchar, procurement_id varchar, procurement_method varchar,
      recipient_id varchar, recipient_name varchar, recipient_kind varchar, corporate_number varchar,
      source_url varchar, published_date date, data_source varchar, derivation_stage varchar,
      confidence double precision, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jp_fiscal_contract_procurement (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, tender_no varchar, contract_no varchar,
      confidence double precision, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jp_fiscal_payment_contract (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, paid_jpy bigint NOT NULL, paid_at date,
      confidence double precision, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jp_fiscal_ownership (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, child_did varchar NOT NULL, parent_did varchar NOT NULL,
      ownership_pct double precision, voting_pct double precision, evidence_kind varchar NOT NULL, evidence_url varchar,
      observed_at date NOT NULL, status varchar NOT NULL, confidence double precision, created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_jp_fiscal_actor_relationship (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, relationship_type varchar NOT NULL,
      subject_did varchar NOT NULL, object_did varchar NOT NULL, role varchar, evidence_kind varchar,
      evidence_url varchar, observed_at date, confidence double precision, payload_json varchar,
      created_at timestamptz NOT NULL
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_source_collection ON vertex_jp_fiscal_source (collection, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_document_source ON vertex_jp_fiscal_document (source_id, collection)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_budget_year ON vertex_jp_fiscal_budget_book (fiscal_year, account_type, doc_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_appropriation_ministry ON vertex_jp_fiscal_appropriation (ministry_did, fiscal_year)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_procurement_issuer ON vertex_jp_fiscal_procurement_bid (issuer_did, opened_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_contract_issuer ON vertex_jp_fiscal_contract (issuer_did, signed_date)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_contract_contractor ON vertex_jp_fiscal_contract (contractor_did, signed_date)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_payment_payee ON vertex_jp_fiscal_payment_record (payee_did, fiscal_year)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_tax_receiver ON vertex_jp_fiscal_tax_payment (receiver_did, period_iso)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_audit_target ON vertex_jp_fiscal_audit_finding (target_did, fiscal_year)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_ubo_child ON vertex_jp_fiscal_beneficial_owner (child_did, observed_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jp_fiscal_statement_speaker ON vertex_jp_fiscal_public_statement (speaker_did, stated_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jp_fiscal_flow_year ON edge_jp_fiscal_flow (fiscal_year, flow_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jp_fiscal_flow_source ON edge_jp_fiscal_flow (source_did, fiscal_year)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jp_fiscal_flow_dest ON edge_jp_fiscal_flow (dest_did, fiscal_year)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jp_fiscal_flow_recipient ON edge_jp_fiscal_flow (recipient_id, fiscal_year)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jp_fiscal_ownership_child ON edge_jp_fiscal_ownership (child_did, observed_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jp_fiscal_actor_rel_subject ON edge_jp_fiscal_actor_relationship (subject_did, relationship_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_jp_fiscal_actor_rel_object ON edge_jp_fiscal_actor_relationship (object_did, relationship_type)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_fiscal_collection_coverage AS
    SELECT collection, COUNT(*) AS row_count, COUNT(DISTINCT source_id) AS source_count
    FROM (
      SELECT 'ai.gftd.apps.jpFiscal.budgetBook' AS collection, source_id FROM vertex_jp_fiscal_budget_book
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.appropriation', source_id FROM vertex_jp_fiscal_appropriation
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.budgetExecution', source_id FROM vertex_jp_fiscal_budget_execution
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.procurementBid', source_id FROM vertex_jp_fiscal_procurement_bid
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.contract', source_id FROM vertex_jp_fiscal_contract
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.paymentRecord', source_id FROM vertex_jp_fiscal_payment_record
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.subsidyGrant', source_id FROM vertex_jp_fiscal_subsidy_grant
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.taxPayment', source_id FROM vertex_jp_fiscal_tax_payment
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.kofuzeiTransfer', source_id FROM vertex_jp_fiscal_kofuzei_transfer
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.lgFinance', source_id FROM vertex_jp_fiscal_lg_finance
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.incorpFinance', source_id FROM vertex_jp_fiscal_incorp_finance
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.programReview', source_id FROM vertex_jp_fiscal_program_review
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.auditFinding', source_id FROM vertex_jp_fiscal_audit_finding
      UNION ALL SELECT 'ai.gftd.apps.jpFiscal.beneficialOwner', source_id FROM vertex_jp_fiscal_beneficial_owner
    ) records
    GROUP BY collection
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_fiscal_flow_by_actor_year AS
    SELECT fiscal_year, flow_type, source_did, dest_did, COUNT(*) AS flow_count, SUM(amount_jpy) AS total_amount_jpy
    FROM edge_jp_fiscal_flow
    GROUP BY fiscal_year, flow_type, source_did, dest_did
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_fiscal_recipient_ranking AS
    SELECT fiscal_year, recipient_id, recipient_name, recipient_kind, corporate_number,
           COUNT(*) AS flow_count, SUM(amount_jpy) AS total_amount_jpy
    FROM edge_jp_fiscal_flow
    WHERE recipient_id IS NOT NULL
    GROUP BY fiscal_year, recipient_id, recipient_name, recipient_kind, corporate_number
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_fiscal_contract_payment_ubo AS
    SELECT
      c.vertex_id AS contract_vertex_id,
      c.contract_no,
      c.issuer_did,
      c.contractor_did,
      c.contractor_jcn,
      c.amount_jpy AS contract_amount_jpy,
      p.vertex_id AS payment_vertex_id,
      p.paid_jpy,
      p.fiscal_year,
      u.parent_did AS beneficial_owner_did,
      u.parent_type AS beneficial_owner_type,
      u.ownership_pct,
      u.status AS ubo_status,
      c.publication_url,
      COALESCE(p.source_url, c.publication_url) AS source_url
    FROM vertex_jp_fiscal_contract c
    LEFT JOIN vertex_jp_fiscal_payment_record p
      ON p.contract_did = c.vertex_id
    LEFT JOIN vertex_jp_fiscal_beneficial_owner u
      ON u.child_did = c.contractor_did
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_fiscal_actor_relationship_degree AS
    SELECT subject_did, relationship_type, COUNT(*) AS outbound_count, COUNT(DISTINCT object_did) AS distinct_object_count
    FROM edge_jp_fiscal_actor_relationship
    GROUP BY subject_did, relationship_type
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_actor_relationship_degree`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_contract_payment_ubo`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_recipient_ranking`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_flow_by_actor_year`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_collection_coverage`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_fiscal_actor_relationship`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_fiscal_ownership`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_fiscal_payment_contract`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_fiscal_contract_procurement`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_fiscal_flow`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_jp_fiscal_evidence`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_public_statement`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_beneficial_owner`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_audit_finding`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_program_review`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_incorp_finance`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_lg_finance`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_kofuzei_transfer`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_tax_payment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_subsidy_grant`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_payment_record`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_contract`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_procurement_bid`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_budget_execution`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_appropriation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_budget_book`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_document`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_jp_fiscal_source`.execute(db);
}
