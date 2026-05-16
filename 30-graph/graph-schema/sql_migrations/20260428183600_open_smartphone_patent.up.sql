CREATE TABLE IF NOT EXISTS vertex_open_smartphone_patent_sep (
      vertex_id VARCHAR PRIMARY KEY,
      patent_no VARCHAR NOT NULL,
      holder_did VARCHAR,
      cpc_codes VARCHAR,
      rat VARCHAR,
      frand_declared BOOLEAN NOT NULL DEFAULT false,
      pool_id VARCHAR,
      priority_date VARCHAR,
      expiry_date VARCHAR,
      jurisdiction_iso3 VARCHAR,
      blocker_status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-patent'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_patent_pool (
      vertex_id VARCHAR PRIMARY KEY,
      pool_id VARCHAR NOT NULL,
      pool_name VARCHAR NOT NULL,
      administrator VARCHAR NOT NULL,
      standards_covered VARCHAR,
      member_count INTEGER,
      license_fee_usd_per_unit DOUBLE PRECISION,
      frand_compliant BOOLEAN NOT NULL DEFAULT true,
      url VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 1,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-patent'
    );

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_open_smartphone_patent_dep (
      vertex_id VARCHAR PRIMARY KEY,
      dep_id VARCHAR NOT NULL,
      component_type VARCHAR NOT NULL,
      component_did VARCHAR,
      patent_no VARCHAR NOT NULL,
      holder_did VARCHAR,
      standard VARCHAR,
      dependency_type VARCHAR NOT NULL,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR NOT NULL DEFAULT 'sys.bpmn.open-smartphone-patent'
    );

FLUSH;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_open_smartphone_patent_free_zone AS
    SELECT
      vertex_id,
      patent_no,
      holder_did,
      rat,
      expiry_date,
      blocker_status
    FROM vertex_open_smartphone_patent_sep
    WHERE expiry_date IS NOT NULL
      AND blocker_status = 'active';

FLUSH;
