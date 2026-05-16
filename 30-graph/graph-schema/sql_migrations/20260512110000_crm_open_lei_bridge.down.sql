DROP MATERIALIZED VIEW IF EXISTS mv_crm_lei_coverage;
DROP VIEW IF EXISTS view_crm_lei_linked_entity;
DROP VIEW IF EXISTS view_crm_lei_pending_resolution;
DROP TABLE IF EXISTS vertex_crm_lei_resolution_run;
DROP INDEX IF EXISTS idx_crm_open_lei_match_status;
DROP INDEX IF EXISTS idx_crm_open_lei_match_lei;
DROP INDEX IF EXISTS idx_crm_open_lei_match_src;
DROP TABLE IF EXISTS edge_crm_open_lei_match;
DROP INDEX IF EXISTS idx_hubspot_company_lei_status;
DROP INDEX IF EXISTS idx_hubspot_company_lei;
DROP INDEX IF EXISTS idx_lawfirm_tenant_lei;
DROP INDEX IF EXISTS idx_lawfirm_lead_lei_status;
DROP INDEX IF EXISTS idx_lawfirm_lead_lei;

ALTER TABLE vertex_hubspot_company DROP COLUMN IF EXISTS lei_verified_at;
ALTER TABLE vertex_hubspot_company DROP COLUMN IF EXISTS lei_match_confidence_permille;
ALTER TABLE vertex_hubspot_company DROP COLUMN IF EXISTS lei_match_status;
ALTER TABLE vertex_hubspot_company DROP COLUMN IF EXISTS lei;

ALTER TABLE vertex_lawfirm_tenant DROP COLUMN IF EXISTS lei_verified_at;
ALTER TABLE vertex_lawfirm_tenant DROP COLUMN IF EXISTS lei_match_confidence_permille;
ALTER TABLE vertex_lawfirm_tenant DROP COLUMN IF EXISTS lei_match_status;
ALTER TABLE vertex_lawfirm_tenant DROP COLUMN IF EXISTS lei;

ALTER TABLE vertex_lawfirm_lead DROP COLUMN IF EXISTS lei_verified_at;
ALTER TABLE vertex_lawfirm_lead DROP COLUMN IF EXISTS lei_match_confidence_permille;
ALTER TABLE vertex_lawfirm_lead DROP COLUMN IF EXISTS lei_match_status;
ALTER TABLE vertex_lawfirm_lead DROP COLUMN IF EXISTS lei;
ALTER TABLE vertex_lawfirm_lead DROP COLUMN IF EXISTS legal_entity_name;
