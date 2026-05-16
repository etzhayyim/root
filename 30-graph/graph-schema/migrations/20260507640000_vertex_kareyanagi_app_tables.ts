import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kareyanagi_listing (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      seller_did VARCHAR,
      product_name VARCHAR,
      price DOUBLE PRECISION,
      currency VARCHAR,
      quantity BIGINT,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kareyanagi_listing_seller ON vertex_kareyanagi_listing (seller_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kareyanagi_listing_status ON vertex_kareyanagi_listing (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kareyanagi_order (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      buyer_did VARCHAR,
      listing_id VARCHAR,
      quantity BIGINT,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kareyanagi_order_buyer ON vertex_kareyanagi_order (buyer_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kareyanagi_order_listing ON vertex_kareyanagi_order (listing_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kareyanagi_order_status ON vertex_kareyanagi_order (status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_kareyanagi_order`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kareyanagi_listing`.execute(db);
}
