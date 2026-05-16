CREATE TABLE IF NOT EXISTS vertex_credit_wallet (
      vertex_id VARCHAR PRIMARY KEY,
      user_id VARCHAR,
      balance BIGINT,
      status VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_credit_transaction (
      vertex_id VARCHAR PRIMARY KEY,
      tx_id VARCHAR,
      user_id VARCHAR,
      tx_type VARCHAR,
      amount BIGINT,
      source VARCHAR,
      source_ref VARCHAR,
      description VARCHAR,
      created_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_credits_af_event (
      vertex_id VARCHAR PRIMARY KEY,
      user_id VARCHAR,
      event_type VARCHAR,
      amount BIGINT,
      ts_ms BIGINT,
      created_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_credit_allocation_preference (
      vertex_id VARCHAR PRIMARY KEY,
      user_id VARCHAR,
      destination_id VARCHAR,
      allocation_bps BIGINT,
      updated_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_credits_public_fund_allocation (
      vertex_id VARCHAR PRIMARY KEY,
      allocation_id VARCHAR,
      spend_tx_id VARCHAR,
      user_id VARCHAR,
      source_action VARCHAR,
      source_ref VARCHAR,
      spend_amount BIGINT,
      service_amount BIGINT,
      public_fund_amount BIGINT,
      public_fund_bps BIGINT,
      destination_project_id VARCHAR,
      destination_id VARCHAR,
      destination_title VARCHAR,
      destination_kind VARCHAR,
      cofog_code VARCHAR,
      created_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_credits_spend_failure (
      vertex_id VARCHAR PRIMARY KEY,
      user_id VARCHAR,
      action VARCHAR,
      cost BIGINT,
      balance BIGINT,
      source_ref VARCHAR,
      created_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_credit_wallet_user ON vertex_credit_wallet (user_id);

CREATE INDEX IF NOT EXISTS idx_credit_tx_user_created ON vertex_credit_transaction (user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_credit_tx_source_ref ON vertex_credit_transaction (source_ref);

CREATE INDEX IF NOT EXISTS idx_credit_af_user_type_ts ON vertex_credits_af_event (user_id, event_type, ts_ms);

CREATE INDEX IF NOT EXISTS idx_credit_pref_user ON vertex_credit_allocation_preference (user_id);

CREATE INDEX IF NOT EXISTS idx_credit_allocation_user_created ON vertex_credits_public_fund_allocation (user_id, created_at);
