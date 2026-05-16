import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_casino_casino (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      city VARCHAR,
      country VARCHAR,
      license_status VARCHAR,
      description VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_casino_casino_city ON vertex_casino_casino (city)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_casino_casino_country ON vertex_casino_casino (country)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_casino_review (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      casino_id VARCHAR,
      reviewer_did VARCHAR,
      rating BIGINT,
      content VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_casino_review_casino_id ON vertex_casino_review (casino_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_casino_review_reviewer ON vertex_casino_review (reviewer_did)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_casino_review`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_casino_casino`.execute(db);
}
