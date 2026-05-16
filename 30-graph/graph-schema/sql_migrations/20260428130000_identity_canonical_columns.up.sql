CREATE TABLE IF NOT EXISTS vertex_signal_identity (
      vertex_id   VARCHAR PRIMARY KEY,
      actor_did   VARCHAR NOT NULL,
      at_did      VARCHAR,
      ik_pub      VARCHAR,
      spk_pub     VARCHAR,
      spk_sig     VARCHAR,
      opk_pubs    VARCHAR,
      org_did     VARCHAR NOT NULL DEFAULT 'anon',
      created_at  VARCHAR NOT NULL,
      _seq        BIGINT,
      sensitivity_ord INTEGER DEFAULT 2,
      owner_did   VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_signal_identity_actor_did
      ON vertex_signal_identity (actor_did);

CREATE INDEX IF NOT EXISTS idx_signal_identity_at_did
      ON vertex_signal_identity (at_did);

CREATE TABLE IF NOT EXISTS vertex_erc725_linked_method (
      vertex_id          VARCHAR PRIMARY KEY,
      actor_did          VARCHAR NOT NULL,
      org_did            VARCHAR NOT NULL DEFAULT 'anon',
      at_did             VARCHAR,
      provider           VARCHAR NOT NULL,
      wallet_address     VARCHAR,
      chain_id           VARCHAR,
      wallet_kind        VARCHAR,
      verification_kind  VARCHAR,
      siwe_hash          VARCHAR,
      linked_at          VARCHAR,
      revoked_at         VARCHAR,
      created_at         VARCHAR NOT NULL,
      _seq               BIGINT,
      sensitivity_ord    INTEGER DEFAULT 1,
      owner_did          VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_erc725_linked_method_actor_did
      ON vertex_erc725_linked_method (actor_did);

CREATE INDEX IF NOT EXISTS idx_erc725_linked_method_wallet_address
      ON vertex_erc725_linked_method (wallet_address);
