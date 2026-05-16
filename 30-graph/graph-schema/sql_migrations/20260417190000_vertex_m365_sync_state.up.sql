CREATE TABLE IF NOT EXISTS vertex_m365_user (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      upn               VARCHAR,
      user_id           VARCHAR,
      display_name      VARCHAR,
      mail              VARCHAR,
      account_enabled   BOOLEAN,
      upn_domain        VARCHAR,
      first_seen_at     VARCHAR,
      last_seen_at      VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      actor_id          VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_m365_sync_state (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      upn                VARCHAR,
      data_kind          VARCHAR,
      last_sync_at       VARCHAR,
      last_received_at   VARCHAR,
      record_count       BIGINT,
      error_count        BIGINT,
      last_error         VARCHAR,
      last_error_at      VARCHAR,
      throttle_until     VARCHAR,
      status             VARCHAR,
      run_id             VARCHAR,
      created_at         VARCHAR,
      updated_at         VARCHAR,
      org_id             VARCHAR,
      actor_id           VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_m365_user_upn ON vertex_m365_user (upn);

CREATE INDEX IF NOT EXISTS idx_m365_user_domain ON vertex_m365_user (upn_domain);

CREATE INDEX IF NOT EXISTS idx_m365_sync_upn_kind ON vertex_m365_sync_state (upn, data_kind);

CREATE INDEX IF NOT EXISTS idx_m365_sync_status ON vertex_m365_sync_state (status);
