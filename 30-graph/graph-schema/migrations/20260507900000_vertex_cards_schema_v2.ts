import { Kysely, sql } from 'kysely';

// ADR-0095: add actor_did / org_did / business-key columns to cards tables
// and create the two missing tables (transaction + dispute).

export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_cards_cardholder ──────────────────────────────────────────────
  await sql`ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS cardholder_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS billing_address VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS org_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cards_cardholder ADD COLUMN IF NOT EXISTS updated_at VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_cardholder_id ON vertex_cards_cardholder (cardholder_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_cardholder_actor_did ON vertex_cards_cardholder (actor_did)`.execute(db);

  // ── vertex_cards_issued_card ─────────────────────────────────────────────
  await sql`ALTER TABLE vertex_cards_issued_card ADD COLUMN IF NOT EXISTS card_id VARCHAR`.execute(db);
  // spending_limit replaces spending_limit_amount (DOUBLE PRECISION, not BIGINT)
  await sql`ALTER TABLE vertex_cards_issued_card ADD COLUMN IF NOT EXISTS spending_limit DOUBLE PRECISION`.execute(db);
  await sql`ALTER TABLE vertex_cards_issued_card ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cards_issued_card ADD COLUMN IF NOT EXISTS org_did VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_issued_card_id ON vertex_cards_issued_card (card_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_issued_card_actor_did ON vertex_cards_issued_card (actor_did)`.execute(db);

  // ── vertex_cards_authorization ───────────────────────────────────────────
  await sql`ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS auth_id VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS merchant VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS actor_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS org_did VARCHAR`.execute(db);
  await sql`ALTER TABLE vertex_cards_authorization ADD COLUMN IF NOT EXISTS updated_at VARCHAR`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_auth_id ON vertex_cards_authorization (auth_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_auth_actor_did ON vertex_cards_authorization (actor_did)`.execute(db);

  // ── vertex_cards_transaction (new) ───────────────────────────────────────
  await sql`
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
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_txn_card_id ON vertex_cards_transaction (card_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_txn_id ON vertex_cards_transaction (txn_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_txn_actor_did ON vertex_cards_transaction (actor_did)`.execute(db);

  // ── vertex_cards_dispute (new) ───────────────────────────────────────────
  await sql`
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
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_dispute_card_id ON vertex_cards_dispute (card_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_dispute_id ON vertex_cards_dispute (dispute_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_dispute_actor_did ON vertex_cards_dispute (actor_did)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_cards_dispute`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cards_transaction`.execute(db);
}
