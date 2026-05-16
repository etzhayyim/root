CREATE TABLE IF NOT EXISTS vertex_contracts_organization (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      did VARCHAR,
      legal_entity_ref VARCHAR,
      country VARCHAR,
      lei VARCHAR,
      national_id VARCHAR,
      name VARCHAR,
      legal_name VARCHAR,
      entity_type VARCHAR,
      isic VARCHAR,
      duns VARCHAR,
      wikidata_qid VARCHAR,
      opencorporates_id VARCHAR,
      status VARCHAR,
      source VARCHAR,
      source_record_id VARCHAR,
      confidence DOUBLE PRECISION,
      last_verified VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_contracts_org_legal_entity_ref
      ON vertex_contracts_organization (legal_entity_ref);

CREATE INDEX IF NOT EXISTS idx_contracts_org_lei
      ON vertex_contracts_organization (lei);

CREATE INDEX IF NOT EXISTS idx_contracts_org_national_id
      ON vertex_contracts_organization (national_id);

CREATE INDEX IF NOT EXISTS idx_contracts_org_did
      ON vertex_contracts_organization (did);

CREATE INDEX IF NOT EXISTS idx_contracts_org_country
      ON vertex_contracts_organization (country);

CREATE TABLE IF NOT EXISTS vertex_contracts_social_contract (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      name VARCHAR,
      constitutional_type VARCHAR,
      jurisdiction VARCHAR,
      adopted_date VARCHAR,
      effective_date VARCHAR,
      scope VARCHAR,
      url VARCHAR,
      un_reg_no VARCHAR,
      source VARCHAR,
      source_record_id VARCHAR,
      confidence DOUBLE PRECISION,
      last_verified VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_contracts_social_contract_jurisdiction
      ON vertex_contracts_social_contract (jurisdiction);

CREATE INDEX IF NOT EXISTS idx_contracts_social_contract_source_record_id
      ON vertex_contracts_social_contract (source_record_id);

CREATE TABLE IF NOT EXISTS edge_contracts_grantedBy (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      contract_type VARCHAR,
      granted_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_contracts_grantedBy_src
      ON edge_contracts_grantedBy (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_contracts_grantedBy_dst
      ON edge_contracts_grantedBy (dst_vid);
