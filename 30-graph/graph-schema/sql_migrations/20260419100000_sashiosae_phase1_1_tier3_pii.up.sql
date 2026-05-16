CREATE TABLE vertex_sashiosae_case_pii (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      case_id            VARCHAR NOT NULL,
      authority_did      VARCHAR NOT NULL,
      debtor_did         VARCHAR NOT NULL,
      debtor_handle      VARCHAR,
      debtor_name        VARCHAR,
      amount             DOUBLE PRECISION NOT NULL,
      currency           VARCHAR NOT NULL DEFAULT 'JPY',
      tax_kind           VARCHAR,
      created_at         TIMESTAMPTZ NOT NULL,
      updated_at         TIMESTAMPTZ
    );

CREATE TABLE vertex_sashiosae_notice_property_pii (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      notice_id          VARCHAR NOT NULL,
      case_id            VARCHAR NOT NULL,
      authority_did      VARCHAR NOT NULL,
      property_type      VARCHAR NOT NULL,
      property_detail    VARCHAR NOT NULL,
      bank_account       VARCHAR,
      real_estate_id     VARCHAR,
      created_at         TIMESTAMPTZ NOT NULL
    );

CREATE TABLE vertex_sashiosae_kanka_winner_pii (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      kanka_id           VARCHAR NOT NULL,
      authority_did      VARCHAR NOT NULL,
      winner_did         VARCHAR,
      winner_handle      VARCHAR,
      cleared_amount     DOUBLE PRECISION,
      currency           VARCHAR NOT NULL DEFAULT 'JPY',
      created_at         TIMESTAMPTZ NOT NULL
    );

CREATE TABLE vertex_sashiosae_authority_audit (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT NOT NULL,
      owner_did          VARCHAR NOT NULL,
      audit_id           VARCHAR NOT NULL,
      authority_did      VARCHAR NOT NULL,
      method_nsid        VARCHAR NOT NULL,
      case_id            VARCHAR,
      target_did         VARCHAR,
      action             VARCHAR NOT NULL,
      lxm_scope          VARCHAR,
      ip_address         VARCHAR,
      user_agent         VARCHAR,
      result             VARCHAR NOT NULL,
      error_code         VARCHAR,
      created_at         TIMESTAMPTZ NOT NULL
    );

CREATE INDEX idx_sashiosae_case_pii_case_id ON vertex_sashiosae_case_pii (case_id);

CREATE INDEX idx_sashiosae_case_pii_debtor ON vertex_sashiosae_case_pii (debtor_did);

CREATE INDEX idx_sashiosae_notice_property_notice ON vertex_sashiosae_notice_property_pii (notice_id);

CREATE INDEX idx_sashiosae_kanka_winner_kanka ON vertex_sashiosae_kanka_winner_pii (kanka_id);

CREATE INDEX idx_sashiosae_audit_authority ON vertex_sashiosae_authority_audit (authority_did, created_at);

CREATE INDEX idx_sashiosae_audit_method ON vertex_sashiosae_authority_audit (method_nsid, created_at);
