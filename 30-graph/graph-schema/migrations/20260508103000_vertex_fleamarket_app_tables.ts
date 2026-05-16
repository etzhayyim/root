import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fleamarket_listing (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      seller_did VARCHAR,
      price DOUBLE PRECISION,
      currency VARCHAR,
      description VARCHAR,
      category VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_fleamarket_listing_seller ON vertex_fleamarket_listing (seller_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_fleamarket_listing_category ON vertex_fleamarket_listing (category)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_fleamarket_listing_status ON vertex_fleamarket_listing (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_fleamarket_transaction (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      listing_id VARCHAR,
      buyer_did VARCHAR,
      seller_did VARCHAR,
      amount DOUBLE PRECISION,
      currency VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_fleamarket_tx_listing ON vertex_fleamarket_transaction (listing_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_fleamarket_tx_buyer ON vertex_fleamarket_transaction (buyer_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_fleamarket_tx_seller ON vertex_fleamarket_transaction (seller_did)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_fleamarket_transaction`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_fleamarket_listing`.execute(db);
}
