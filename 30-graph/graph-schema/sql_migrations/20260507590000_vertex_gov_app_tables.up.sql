CREATE TABLE IF NOT EXISTS vertex_gov_official_agency (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      name_local VARCHAR,
      jurisdiction VARCHAR,
      branch VARCHAR,
      level VARCHAR,
      cofog VARCHAR,
      parent_agency_did VARCHAR,
      established_at VARCHAR,
      legal_basis VARCHAR,
      website_uri VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gov_agency_jurisdiction ON vertex_gov_official_agency (jurisdiction);

CREATE INDEX IF NOT EXISTS idx_gov_agency_branch ON vertex_gov_official_agency (branch);

CREATE INDEX IF NOT EXISTS idx_gov_agency_cofog ON vertex_gov_official_agency (cofog);

CREATE TABLE IF NOT EXISTS vertex_gov_official (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      agency_did VARCHAR,
      person_did VARCHAR,
      role VARCHAR,
      appointed_at VARCHAR,
      term_ends_at VARCHAR,
      appointed_by_did VARCHAR,
      confirmation_process VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gov_official_agency_did ON vertex_gov_official (agency_did);

CREATE INDEX IF NOT EXISTS idx_gov_official_person_did ON vertex_gov_official (person_did);

CREATE TABLE IF NOT EXISTS vertex_gov_consult (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      requester_did VARCHAR,
      domain VARCHAR,
      category VARCHAR,
      query VARCHAR,
      municipality_code VARCHAR,
      priority VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gov_consult_requester_did ON vertex_gov_consult (requester_did);

CREATE INDEX IF NOT EXISTS idx_gov_consult_domain ON vertex_gov_consult (domain);

CREATE INDEX IF NOT EXISTS idx_gov_consult_status ON vertex_gov_consult (status);
