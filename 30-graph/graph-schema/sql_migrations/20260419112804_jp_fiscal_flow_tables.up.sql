CREATE TABLE IF NOT EXISTS vertex_etzhayyim_beneficial_owner (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      child_did         VARCHAR,
      child_jcn         VARCHAR,
      parent_did        VARCHAR,
      parent_type       VARCHAR,
      ownership_pct     DOUBLE PRECISION,
      voting_pct        DOUBLE PRECISION,
      evidence_kind     VARCHAR,
      evidence_url      VARCHAR,
      observed_at       DATE,
      status            VARCHAR,
      opacity_reason    VARCHAR,
      pii_tier          BIGINT,
      created_at        VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_beneficial_owner_child_did ON vertex_etzhayyim_beneficial_owner (child_did);

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_beneficial_owner_parent_did ON vertex_etzhayyim_beneficial_owner (parent_did);

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_beneficial_owner_status ON vertex_etzhayyim_beneficial_owner (status);

CREATE TABLE IF NOT EXISTS edge_etzhayyim_fiscal_flow (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      from_did           VARCHAR,
      to_did             VARCHAR,
      stage              VARCHAR,
      derivation_stage   VARCHAR,
      fiscal_year        BIGINT,
      amount_jpy         BIGINT,
      basis              VARCHAR,
      program_code       VARCHAR,
      source_record_uri  VARCHAR,
      source_url         VARCHAR,
      observed_at        DATE
    );

CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_fiscal_flow_from ON edge_etzhayyim_fiscal_flow (from_did, fiscal_year);

CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_fiscal_flow_to ON edge_etzhayyim_fiscal_flow (to_did, fiscal_year);

CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_fiscal_flow_stage ON edge_etzhayyim_fiscal_flow (stage, fiscal_year);

CREATE TABLE IF NOT EXISTS edge_etzhayyim_ownership (
      edge_id            VARCHAR PRIMARY KEY,
      src_vid            VARCHAR,
      dst_vid            VARCHAR,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      parent_did         VARCHAR,
      child_did          VARCHAR,
      ownership_pct      DOUBLE PRECISION,
      voting_pct         DOUBLE PRECISION,
      evidence_kind      VARCHAR,
      evidence_url       VARCHAR,
      observed_at        DATE
    );

CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_ownership_child ON edge_etzhayyim_ownership (child_did, observed_at);

CREATE INDEX IF NOT EXISTS idx_edge_etzhayyim_ownership_parent ON edge_etzhayyim_ownership (parent_did, observed_at);
