CREATE TABLE IF NOT EXISTS vertex_robotics_ems_company (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      company_id VARCHAR,
      legal_name VARCHAR,
      display_name VARCHAR,
      country_code VARCHAR,
      region VARCHAR,
      website_url VARCHAR,
      marketplace_url VARCHAR,
      source VARCHAR,
      source_ref VARCHAR,
      as_of_date VARCHAR,
      moq BIGINT,
      lead_time_days BIGINT,
      risk_level VARCHAR,
      evidence_json VARCHAR,
      risk_flags_json VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_robotics_ems_company_id ON vertex_robotics_ems_company (company_id);

CREATE INDEX IF NOT EXISTS idx_robotics_ems_company_region ON vertex_robotics_ems_company (country_code, region);

CREATE INDEX IF NOT EXISTS idx_robotics_ems_company_risk ON vertex_robotics_ems_company (risk_level);

CREATE TABLE IF NOT EXISTS vertex_robotics_ems_capability (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      capability_id VARCHAR,
      capability_kind VARCHAR,
      label VARCHAR,
      standard VARCHAR,
      evidence_required BOOLEAN,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_robotics_ems_capability_kind ON vertex_robotics_ems_capability (capability_kind);

CREATE INDEX IF NOT EXISTS idx_robotics_ems_capability_id ON vertex_robotics_ems_capability (capability_id);

CREATE TABLE IF NOT EXISTS vertex_robotics_ems_certification (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      certification_id VARCHAR,
      label VARCHAR,
      issuer VARCHAR,
      standard VARCHAR,
      expires_at VARCHAR,
      evidence_blob_key VARCHAR,
      verification_status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_robotics_ems_certification_id ON vertex_robotics_ems_certification (certification_id);

CREATE INDEX IF NOT EXISTS idx_robotics_ems_certification_status ON vertex_robotics_ems_certification (verification_status);

CREATE TABLE IF NOT EXISTS edge_robotics_ems_company_has_capability (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      company_id VARCHAR,
      capability_id VARCHAR,
      evidence_status VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_robotics_ems_cap_src ON edge_robotics_ems_company_has_capability (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_robotics_ems_cap_dst ON edge_robotics_ems_company_has_capability (dst_vid);

CREATE TABLE IF NOT EXISTS edge_robotics_ems_company_has_certification (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      company_id VARCHAR,
      certification_id VARCHAR,
      verification_status VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_robotics_ems_cert_src ON edge_robotics_ems_company_has_certification (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_robotics_ems_cert_dst ON edge_robotics_ems_company_has_certification (dst_vid);

CREATE TABLE IF NOT EXISTS edge_robotics_ems_company_matches_rfq (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      company_id VARCHAR,
      rfq_id VARCHAR,
      package_id VARCHAR,
      match_score DOUBLE PRECISION,
      decision VARCHAR,
      missing_capabilities_json VARCHAR,
      next_evidence_json VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_robotics_ems_match_company ON edge_robotics_ems_company_matches_rfq (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_robotics_ems_match_rfq ON edge_robotics_ems_company_matches_rfq (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_robotics_ems_match_score ON edge_robotics_ems_company_matches_rfq (decision, match_score);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_robotics_ems_company_readiness AS
      SELECT
        c.vertex_id AS company_vid,
        c.company_id,
        c.display_name,
        c.country_code,
        c.region,
        c.risk_level,
        COUNT(DISTINCT cap.dst_vid) AS capability_count,
        COUNT(DISTINCT cert.dst_vid) AS certification_count,
        COUNT(DISTINCT CASE WHEN cert.verification_status = 'verified' THEN cert.dst_vid ELSE NULL END) AS verified_certification_count,
        MAX(c._seq) AS _seq
      FROM vertex_robotics_ems_company c
      LEFT JOIN edge_robotics_ems_company_has_capability cap ON cap.src_vid = c.vertex_id
      LEFT JOIN edge_robotics_ems_company_has_certification cert ON cert.src_vid = c.vertex_id
      GROUP BY c.vertex_id, c.company_id, c.display_name, c.country_code, c.region, c.risk_level;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_robotics_ems_rfq_shortlist AS
      SELECT
        m.rfq_id,
        m.package_id,
        c.company_id,
        c.display_name,
        c.country_code,
        c.region,
        m.match_score,
        m.decision,
        m.missing_capabilities_json,
        m.next_evidence_json,
        MAX(m._seq) AS _seq
      FROM edge_robotics_ems_company_matches_rfq m
      JOIN vertex_robotics_ems_company c ON c.vertex_id = m.src_vid
      WHERE m.decision IN ('shortlist', 'review')
      GROUP BY m.rfq_id, m.package_id, c.company_id, c.display_name, c.country_code,
               c.region, m.match_score, m.decision, m.missing_capabilities_json,
               m.next_evidence_json;
