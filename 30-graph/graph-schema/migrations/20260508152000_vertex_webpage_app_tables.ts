import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_webpage_page (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_webpage_page_status ON vertex_webpage_page (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_webpage_publish (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      page_id VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_webpage_publish_page_id ON vertex_webpage_publish (page_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_webpage_publish_status ON vertex_webpage_publish (status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_webpage_publish`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_webpage_page`.execute(db);
}
