import { Kysely, sql } from 'kysely';

// ADR-0095 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_tia_signal (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      signal_text VARCHAR,
      source VARCHAR,
      classification VARCHAR,
      risk_score DOUBLE PRECISION,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tia_signal_id ON vertex_tia_signal (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tia_signal_source ON vertex_tia_signal (source)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_tia_signal_classification ON vertex_tia_signal (classification)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_tia_signal`.execute(db);
}
