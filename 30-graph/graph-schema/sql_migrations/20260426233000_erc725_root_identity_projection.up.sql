CREATE TABLE IF NOT EXISTS vertex_erc725_root_identity (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      root_did VARCHAR,
      root_did_hash VARCHAR,
      root_identity_addr VARCHAR,
      chain_id BIGINT,
      registry_addr VARCHAR,
      controller_addr VARCHAR,

      source VARCHAR,
      status VARCHAR,

      org_id VARCHAR DEFAULT 'anon',
      user_id VARCHAR DEFAULT 'anon',
      actor_id VARCHAR DEFAULT '',
      created_at VARCHAR,
      updated_at VARCHAR
    );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_erc725_facade_did (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,

      root_did VARCHAR,
      root_did_hash VARCHAR,
      facade_did VARCHAR,
      facade_did_hash VARCHAR,
      facade_method VARCHAR,
      root_identity_addr VARCHAR,
      chain_id BIGINT,
      registry_addr VARCHAR,
      status VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

FLUSH;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN root_did VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN root_did_hash VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN root_identity_addr VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN facade_did VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN facade_did_hash VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN identity_method VARCHAR;

ALTER TABLE vertex_etzhayyim_identity ADD COLUMN migration_status VARCHAR;

FLUSH;

ALTER TABLE vertex_claim_stake ADD COLUMN root_did VARCHAR;

ALTER TABLE vertex_claim_stake ADD COLUMN root_did_hash VARCHAR;

ALTER TABLE vertex_claim_stake ADD COLUMN root_identity_addr VARCHAR;

ALTER TABLE vertex_claim_stake ADD COLUMN legacy_claimant_did VARCHAR;

FLUSH;

ALTER TABLE vertex_claim_challenge ADD COLUMN root_did VARCHAR;

ALTER TABLE vertex_claim_challenge ADD COLUMN root_did_hash VARCHAR;

ALTER TABLE vertex_claim_challenge ADD COLUMN root_identity_addr VARCHAR;

ALTER TABLE vertex_claim_challenge ADD COLUMN legacy_challenger_did VARCHAR;

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_erc725_root_identity_hash
    ON vertex_erc725_root_identity (root_did_hash);

CREATE INDEX IF NOT EXISTS idx_vertex_erc725_root_identity_addr
    ON vertex_erc725_root_identity (root_identity_addr);

CREATE INDEX IF NOT EXISTS idx_edge_erc725_facade_hash
    ON edge_erc725_facade_did (facade_did_hash);

CREATE INDEX IF NOT EXISTS idx_edge_erc725_facade_root_hash
    ON edge_erc725_facade_did (root_did_hash);

CREATE INDEX IF NOT EXISTS idx_vertex_etzhayyim_identity_root_hash
    ON vertex_etzhayyim_identity (root_did_hash);

CREATE INDEX IF NOT EXISTS idx_vertex_claim_stake_root_hash
    ON vertex_claim_stake (root_did_hash);

CREATE INDEX IF NOT EXISTS idx_vertex_claim_challenge_root_hash
    ON vertex_claim_challenge (root_did_hash);

FLUSH;
