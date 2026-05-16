DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_actor_relationship_degree;

DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_contract_payment_ubo;

DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_recipient_ranking;

DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_flow_by_actor_year;

DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_collection_coverage;

DROP TABLE IF EXISTS edge_jp_fiscal_actor_relationship;

DROP TABLE IF EXISTS edge_jp_fiscal_ownership;

DROP TABLE IF EXISTS edge_jp_fiscal_payment_contract;

DROP TABLE IF EXISTS edge_jp_fiscal_contract_procurement;

DROP TABLE IF EXISTS edge_jp_fiscal_flow;

DROP TABLE IF EXISTS edge_jp_fiscal_evidence;

DROP TABLE IF EXISTS vertex_jp_fiscal_public_statement;

DROP TABLE IF EXISTS vertex_jp_fiscal_beneficial_owner;

DROP TABLE IF EXISTS vertex_jp_fiscal_audit_finding;

DROP TABLE IF EXISTS vertex_jp_fiscal_program_review;

DROP TABLE IF EXISTS vertex_jp_fiscal_incorp_finance;

DROP TABLE IF EXISTS vertex_jp_fiscal_lg_finance;

DROP TABLE IF EXISTS vertex_jp_fiscal_kofuzei_transfer;

DROP TABLE IF EXISTS vertex_jp_fiscal_tax_payment;

DROP TABLE IF EXISTS vertex_jp_fiscal_subsidy_grant;

DROP TABLE IF EXISTS vertex_jp_fiscal_payment_record;

DROP TABLE IF EXISTS vertex_jp_fiscal_contract;

DROP TABLE IF EXISTS vertex_jp_fiscal_procurement_bid;

DROP TABLE IF EXISTS vertex_jp_fiscal_budget_execution;

DROP TABLE IF EXISTS vertex_jp_fiscal_appropriation;

DROP TABLE IF EXISTS vertex_jp_fiscal_budget_book;

DROP TABLE IF EXISTS vertex_jp_fiscal_document;

DROP TABLE IF EXISTS vertex_jp_fiscal_source;
