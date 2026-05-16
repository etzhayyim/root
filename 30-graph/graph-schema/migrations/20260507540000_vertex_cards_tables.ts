import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cards_cardholder (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      user_id VARCHAR,
      name VARCHAR,
      email VARCHAR,
      phone VARCHAR,
      auth_tier VARCHAR,
      stripe_cardholder_id VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_cardholder_user_id ON vertex_cards_cardholder (user_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_cardholder_stripe_id ON vertex_cards_cardholder (stripe_cardholder_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cards_issued_card (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      cardholder_id VARCHAR,
      user_id VARCHAR,
      card_type VARCHAR,
      last_four VARCHAR,
      currency VARCHAR,
      spending_limit_amount BIGINT,
      spending_limit_interval VARCHAR,
      stripe_card_id VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_issued_card_user_id ON vertex_cards_issued_card (user_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_issued_card_cardholder ON vertex_cards_issued_card (cardholder_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_issued_card_stripe_card_id ON vertex_cards_issued_card (stripe_card_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cards_authorization (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      card_id VARCHAR,
      user_id VARCHAR,
      stripe_card_id VARCHAR,
      amount BIGINT,
      currency VARCHAR,
      decision VARCHAR,
      reason VARCHAR,
      available_before BIGINT,
      available_after BIGINT,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_auth_user_created ON vertex_cards_authorization (user_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_auth_card_created ON vertex_cards_authorization (card_id, created_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_auth_decision ON vertex_cards_authorization (decision)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cards_credit_allocation (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      card_id VARCHAR,
      user_id VARCHAR,
      amount BIGINT,
      allocated_total BIGINT,
      consumed_total BIGINT,
      available_total BIGINT,
      destination_id VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_alloc_card_created ON vertex_cards_credit_allocation (card_id, created_at)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cards_credit_consumption (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      card_id VARCHAR,
      user_id VARCHAR,
      stripe_card_id VARCHAR,
      amount BIGINT,
      allocated_total BIGINT,
      consumed_total BIGINT,
      available_total BIGINT,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_cards_consumption_card_created ON vertex_cards_credit_consumption (card_id, created_at)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_cards_credit_consumption`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cards_credit_allocation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cards_authorization`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cards_issued_card`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cards_cardholder`.execute(db);
}
