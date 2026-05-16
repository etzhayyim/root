import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oshiete_question (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      body VARCHAR,
      topic VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_oshiete_question_topic ON vertex_oshiete_question (topic)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_oshiete_question_status ON vertex_oshiete_question (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_oshiete_question_actor_did ON vertex_oshiete_question (actor_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_oshiete_answer (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      question_id VARCHAR,
      body VARCHAR,
      vote_count BIGINT,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_oshiete_answer_question_id ON vertex_oshiete_answer (question_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_oshiete_answer_actor_did ON vertex_oshiete_answer (actor_did)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_oshiete_answer`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_oshiete_question`.execute(db);
}
