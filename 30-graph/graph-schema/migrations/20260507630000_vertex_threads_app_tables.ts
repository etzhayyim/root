import { Kysely, sql } from 'kysely';

// ADR-0095 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_threads_thread (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      author_did VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_threads_thread_id ON vertex_threads_thread (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_threads_thread_status ON vertex_threads_thread (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_threads_thread_author_did ON vertex_threads_thread (author_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_threads_reply (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      thread_id VARCHAR,
      author_did VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_threads_reply_id ON vertex_threads_reply (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_threads_reply_thread_id ON vertex_threads_reply (thread_id)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_threads_reply`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_threads_thread`.execute(db);
}
