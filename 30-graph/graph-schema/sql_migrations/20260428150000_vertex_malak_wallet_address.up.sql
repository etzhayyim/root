CREATE TABLE IF NOT EXISTS vertex_malak_wallet_address (
      vertex_id       VARCHAR NOT NULL PRIMARY KEY,
      rkey            VARCHAR NOT NULL,
      repo            VARCHAR NOT NULL,
      did             VARCHAR NOT NULL,
      chain           VARCHAR NOT NULL,
      address         VARCHAR NOT NULL,
      actor_node_id   VARCHAR NOT NULL,
      label           VARCHAR NOT NULL DEFAULT '',
      confidence      BIGINT  NOT NULL DEFAULT 70,
      evidence        VARCHAR NOT NULL DEFAULT '',
      linked_at       VARCHAR NOT NULL,
      sensitivity_ord BIGINT  NOT NULL DEFAULT 100,
      owner_did       VARCHAR NOT NULL,
      created_date    DATE    NOT NULL
    );

FLUSH;

CREATE TABLE IF NOT EXISTS edge_malak_controls_wallet (
      edge_id         VARCHAR NOT NULL PRIMARY KEY,
      src_vid         VARCHAR NOT NULL,
      dst_vid         VARCHAR NOT NULL,
      sensitivity_ord BIGINT  NOT NULL DEFAULT 100,
      owner_did       VARCHAR NOT NULL,
      created_date    DATE    NOT NULL
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_malak_wallet_address
      ON vertex_malak_wallet_address (address);

CREATE INDEX IF NOT EXISTS idx_malak_wallet_chain_address
      ON vertex_malak_wallet_address (chain, address);

CREATE INDEX IF NOT EXISTS idx_malak_controls_wallet_src
      ON edge_malak_controls_wallet (src_vid);

CREATE INDEX IF NOT EXISTS idx_malak_controls_wallet_dst
      ON edge_malak_controls_wallet (dst_vid);

FLUSH;
