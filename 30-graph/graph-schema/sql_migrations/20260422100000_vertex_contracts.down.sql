DROP INDEX IF EXISTS idx_edge_contracts_grantedBy_dst;

DROP INDEX IF EXISTS idx_edge_contracts_grantedBy_src;

DROP TABLE IF EXISTS edge_contracts_grantedBy;

DROP INDEX IF EXISTS idx_contracts_social_contract_source_record_id;

DROP INDEX IF EXISTS idx_contracts_social_contract_jurisdiction;

DROP TABLE IF EXISTS vertex_contracts_social_contract;

DROP INDEX IF EXISTS idx_contracts_org_country;

DROP INDEX IF EXISTS idx_contracts_org_did;

DROP INDEX IF EXISTS idx_contracts_org_national_id;

DROP INDEX IF EXISTS idx_contracts_org_lei;

DROP INDEX IF EXISTS idx_contracts_org_legal_entity_ref;

DROP TABLE IF EXISTS vertex_contracts_organization;
