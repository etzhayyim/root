CREATE TABLE vertex_fukkou_budget_flow (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      rkey              VARCHAR NOT NULL,
      flow_id           VARCHAR NOT NULL,
      fiscal_year       VARCHAR NOT NULL,
      source_did        VARCHAR NOT NULL,
      source_kind       VARCHAR NOT NULL,
      destination_did   VARCHAR NOT NULL,
      destination_kind  VARCHAR NOT NULL,
      category          VARCHAR NOT NULL,
      sub_category      VARCHAR,
      amount_jpy        DOUBLE PRECISION NOT NULL,
      amount_bucket     VARCHAR NOT NULL,
      effective_date    TIMESTAMPTZ NOT NULL,
      legal_basis       VARCHAR,
      narrative         VARCHAR,
      source_url        VARCHAR,
      created_at        TIMESTAMPTZ NOT NULL
    );

CREATE TABLE edge_fukkou_taxed_to (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR NOT NULL,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      fiscal_year       VARCHAR NOT NULL,
      tax_code          VARCHAR NOT NULL,
      amount_jpy        DOUBLE PRECISION NOT NULL,
      taxpayer_count    BIGINT,
      created_at        TIMESTAMPTZ NOT NULL
    );

CREATE TABLE edge_fukkou_disbursed_to (
      edge_id              VARCHAR PRIMARY KEY,
      src_vid              VARCHAR NOT NULL,
      dst_vid              VARCHAR NOT NULL,
      _seq                 BIGINT NOT NULL,
      owner_did            VARCHAR NOT NULL,
      fiscal_year          VARCHAR NOT NULL,
      disbursement_kind    VARCHAR NOT NULL,
      amount_jpy           DOUBLE PRECISION NOT NULL,
      recipient_category   VARCHAR NOT NULL,
      recipient_lei        VARCHAR,
      recipient_houjin_no  VARCHAR,
      contract_number      VARCHAR,
      created_at           TIMESTAMPTZ NOT NULL
    );

CREATE TABLE vertex_fukkou_taxpayer_stat (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT NOT NULL,
      owner_did         VARCHAR NOT NULL,
      fiscal_year       VARCHAR NOT NULL,
      tax_code          VARCHAR NOT NULL,
      payer_category    VARCHAR NOT NULL,
      payer_count       BIGINT NOT NULL,
      total_amount_jpy  DOUBLE PRECISION NOT NULL,
      created_at        TIMESTAMPTZ NOT NULL
    );

CREATE INDEX idx_fukkou_flow_fy_category ON vertex_fukkou_budget_flow (fiscal_year, category);

CREATE INDEX idx_fukkou_flow_source ON vertex_fukkou_budget_flow (source_did, fiscal_year);

CREATE INDEX idx_fukkou_flow_destination ON vertex_fukkou_budget_flow (destination_did, fiscal_year);

CREATE INDEX idx_fukkou_taxed_fy ON edge_fukkou_taxed_to (fiscal_year, tax_code);

CREATE INDEX idx_fukkou_disbursed_fy ON edge_fukkou_disbursed_to (fiscal_year, recipient_category);

CREATE INDEX idx_fukkou_taxpayer_fy ON vertex_fukkou_taxpayer_stat (fiscal_year, tax_code);

CREATE MATERIALIZED VIEW mv_fukkou_flow_by_category AS
    SELECT
      fiscal_year,
      category,
      source_kind,
      destination_kind,
      COUNT(*)           AS flow_count,
      SUM(amount_jpy)    AS total_jpy
    FROM vertex_fukkou_budget_flow
    GROUP BY fiscal_year, category, source_kind, destination_kind;
