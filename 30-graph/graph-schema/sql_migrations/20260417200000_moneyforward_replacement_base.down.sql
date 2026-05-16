DROP VIEW IF EXISTS view_kaikei_ap_bill_upcoming;

DROP VIEW IF EXISTS view_keiyaku_active_agreements;

DROP VIEW IF EXISTS view_kousuu_project_burn;

DROP VIEW IF EXISTS view_seikyu_invoice_aging;

DROP MATERIALIZED VIEW IF EXISTS mv_kaikei_trial_balance;

DROP TABLE IF EXISTS edge_asset_to_depreciation;

DROP TABLE IF EXISTS edge_time_entry_to_invoice;

DROP TABLE IF EXISTS edge_agreement_to_invoice;

DROP TABLE IF EXISTS edge_invoice_to_project;

DROP TABLE IF EXISTS edge_journal_entry_source;

DROP TABLE IF EXISTS vertex_atrecord_kousuu_cost_rate;

DROP TABLE IF EXISTS vertex_atrecord_kousuu_time_entry;

DROP TABLE IF EXISTS vertex_atrecord_kousuu_project;

DROP TABLE IF EXISTS vertex_atrecord_keiyaku_agreement;

DROP TABLE IF EXISTS vertex_atrecord_seikyu_invoice;

DROP TABLE IF EXISTS vertex_atrecord_seikyu_customer;

DROP TABLE IF EXISTS vertex_atrecord_kaikei_ap_bill;

DROP TABLE IF EXISTS vertex_atrecord_kaikei_fixed_asset;

DROP TABLE IF EXISTS vertex_atrecord_kaikei_bank_transaction;

DROP TABLE IF EXISTS vertex_atrecord_kaikei_journal_entry;

DROP TABLE IF EXISTS vertex_atrecord_kaikei_account;
