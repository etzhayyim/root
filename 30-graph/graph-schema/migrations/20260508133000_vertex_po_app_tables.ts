import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_po_purchase_order (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      supplier_id VARCHAR,
      total_amount DOUBLE PRECISION,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_po_purchase_order_supplier_id ON vertex_po_purchase_order (supplier_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_po_purchase_order_status ON vertex_po_purchase_order (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_po_purchase_order_actor_did ON vertex_po_purchase_order (actor_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_po_supplier (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      contact_email VARCHAR,
      address VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_po_supplier_status ON vertex_po_supplier (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_po_supplier_actor_did ON vertex_po_supplier (actor_did)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_po_supplier`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_po_purchase_order`.execute(db);
}
