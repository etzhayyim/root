import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wire_transfer (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      from_did VARCHAR,
      to_did VARCHAR,
      amount DOUBLE PRECISION,
      currency VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wire_transfer_from_did ON vertex_wire_transfer (from_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wire_transfer_to_did ON vertex_wire_transfer (to_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wire_transfer_status ON vertex_wire_transfer (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wire_message (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      from_did VARCHAR,
      to_did VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wire_message_from_did ON vertex_wire_message (from_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wire_message_to_did ON vertex_wire_message (to_did)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_wire_message`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_wire_transfer`.execute(db);
}
