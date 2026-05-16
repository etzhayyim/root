CREATE TABLE IF NOT EXISTS vertex_claim_stake (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR NOT NULL,
      claim_hash VARCHAR,
      did_hash VARCHAR,
      at_record_cid VARCHAR,
      claimant_addr VARCHAR,
      claimant_did VARCHAR,

      bond VARCHAR,
      bond_wei_dec VARCHAR,
      chain_id BIGINT,
      escrow_addr VARCHAR,
      claim_type VARCHAR,
      arbiter VARCHAR,

      claim_text VARCHAR,
      claim_text_len BIGINT,

      challenge_period_sec BIGINT,
      posted_at VARCHAR,
      window_closes_at VARCHAR,

      state VARCHAR,
      outcome VARCHAR,
      settled_at VARCHAR,
      settle_tx_hash VARCHAR,

      claimant_payout VARCHAR,
      challenger_payout VARCHAR,
      treasury_amount VARCHAR,
      reward_amount VARCHAR,

      org_id VARCHAR DEFAULT 'anon',
      user_id VARCHAR DEFAULT 'anon',
      actor_id VARCHAR DEFAULT '',
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_claim_id ON vertex_claim_stake (claim_id);

CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_claimant ON vertex_claim_stake (claimant_did);

CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_state ON vertex_claim_stake (state);

CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_window_closes ON vertex_claim_stake (window_closes_at);

CREATE TABLE IF NOT EXISTS vertex_claim_challenge (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR NOT NULL,
      challenger_did_hash VARCHAR,
      challenger_did VARCHAR,
      challenger_addr VARCHAR,
      counter_bond VARCHAR,
      counter_bond_wei_dec VARCHAR,
      rebuttal VARCHAR,
      rebuttal_len BIGINT,
      posted_at VARCHAR,
      challenge_tx_hash VARCHAR,

      org_id VARCHAR DEFAULT 'anon',
      user_id VARCHAR DEFAULT 'anon',
      actor_id VARCHAR DEFAULT '',
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_claim_challenge_claim_id ON vertex_claim_challenge (claim_id);

CREATE INDEX IF NOT EXISTS idx_vertex_claim_challenge_challenger ON vertex_claim_challenge (challenger_did);

CREATE TABLE IF NOT EXISTS vertex_claim_resolution (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR NOT NULL,
      outcome VARCHAR,
      rationale VARCHAR,
      tx_hash VARCHAR,
      arbiter_addr VARCHAR,
      claimant_payout VARCHAR,
      challenger_payout VARCHAR,
      treasury_amount VARCHAR,
      reward_amount VARCHAR,
      settled_at VARCHAR,

      org_id VARCHAR DEFAULT 'anon',
      user_id VARCHAR DEFAULT 'anon',
      actor_id VARCHAR DEFAULT '',
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_claim_resolution_claim_id ON vertex_claim_resolution (claim_id);

CREATE INDEX IF NOT EXISTS idx_vertex_claim_resolution_outcome ON vertex_claim_resolution (outcome);

CREATE TABLE IF NOT EXISTS edge_claim_challenge_for (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR,
      counter_bond VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_claim_challenge_for_dst ON edge_claim_challenge_for (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_claim_challenge_for_src ON edge_claim_challenge_for (src_vid);

CREATE TABLE IF NOT EXISTS edge_claim_resolution_for (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      claim_id VARCHAR,
      outcome VARCHAR,
      created_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_claim_resolution_for_dst ON edge_claim_resolution_for (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_claim_resolution_for_src ON edge_claim_resolution_for (src_vid);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_claim_stake_outcomes AS
    SELECT state,
           COUNT(*)                                              AS claim_count,
           SUM(CASE WHEN bond IS NULL THEN 0 ELSE 1 END)         AS bond_set_count
      FROM vertex_claim_stake
     GROUP BY state;
