import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_harai_payment (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      payer_did VARCHAR,
      payee_did VARCHAR,
      amount DOUBLE PRECISION,
      currency VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_harai_payment_payer ON vertex_harai_payment (payer_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_harai_payment_payee ON vertex_harai_payment (payee_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_harai_payment_status ON vertex_harai_payment (status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_harai_payment`.execute(db);
}
