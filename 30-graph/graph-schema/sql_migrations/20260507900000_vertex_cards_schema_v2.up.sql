ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS cardholder_id VARCHAR;

ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS billing_address VARCHAR;

ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS actor_did VARCHAR;

ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS org_did VARCHAR;

ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS updated_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_cards_cardholder_id ON vertex_cards_cardholder (cardholder_id);

CREATE INDEX IF NOT EXISTS idx_cards_cardholder_actor_did ON vertex_cards_cardholder (actor_did);

ALTER TABLE vertex_cards_issued_card ADD COLUMN IF NOT EXISTS card_id VARCHAR;

ALTER TABLE vertex_cards_issued_card ADD COLUMN IF NOT EXISTS spending_limit DOUBLE PRECISION;

ALTER TABLE vertex_cards_issued_card ADD COLUMN IF NOT EXISTS actor_did VARCHAR;

ALTER TABLE vertex_cards_issued_card ADD COLUMN IF NOT EXISTS org_did VARCHAR;

CREATE INDEX IF NOT EXISTS idx_cards_issued_card_id ON vertex_cards_issued_card (card_id);

CREATE INDEX IF NOT EXISTS idx_cards_issued_card_actor_did ON vertex_cards_issued_card (actor_did);

ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS auth_id VARCHAR;

ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS merchant VARCHAR;

ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS actor_did VARCHAR;

ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS org_did VARCHAR;

ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS updated_at VARCHAR;

CREATE INDEX IF NOT EXISTS idx_cards_auth_id ON vertex_cards_authorization (auth_id);

CREATE INDEX IF NOT EXISTS idx_cards_auth_actor_did ON vertex_cards_authorization (actor_did);

CREATE TABLE IF NOT EXISTS vertex_cards_transaction (
      vertex_id      VARCHAR PRIMARY KEY,
      _seq           BIGINT,
      created_date   DATE,
      sensitivity_ord BIGINT,
      txn_id         VARCHAR,
      card_id        VARCHAR,
      merchant       VARCHAR,
      amount         DOUBLE PRECISION,
      currency       VARCHAR,
      status         VARCHAR,
      actor_did      VARCHAR,
      org_did        VARCHAR,
      created_at     VARCHAR,
      updated_at     VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_cards_txn_card_id ON vertex_cards_transaction (card_id);

CREATE INDEX IF NOT EXISTS idx_cards_txn_id ON vertex_cards_transaction (txn_id);

CREATE INDEX IF NOT EXISTS idx_cards_txn_actor_did ON vertex_cards_transaction (actor_did);

CREATE TABLE IF NOT EXISTS vertex_cards_dispute (
      vertex_id      VARCHAR PRIMARY KEY,
      _seq           BIGINT,
      created_date   DATE,
      sensitivity_ord BIGINT,
      dispute_id     VARCHAR,
      card_id        VARCHAR,
      txn_id         VARCHAR,
      reason         VARCHAR,
      status         VARCHAR,
      actor_did      VARCHAR,
      org_did        VARCHAR,
      created_at     VARCHAR,
      updated_at     VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_cards_dispute_card_id ON vertex_cards_dispute (card_id);

CREATE INDEX IF NOT EXISTS idx_cards_dispute_id ON vertex_cards_dispute (dispute_id);

CREATE INDEX IF NOT EXISTS idx_cards_dispute_actor_did ON vertex_cards_dispute (actor_did);
