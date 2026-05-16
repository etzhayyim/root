import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_games_title (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      genre VARCHAR,
      publisher_did VARCHAR,
      platform VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_games_title_genre ON vertex_games_title (genre)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_games_title_publisher ON vertex_games_title (publisher_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_games_score (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title_id VARCHAR,
      player_did VARCHAR,
      score BIGINT,
      level VARCHAR,
      mode VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_games_score_title_id ON vertex_games_score (title_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_games_score_player ON vertex_games_score (player_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_games_score_value ON vertex_games_score (score)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_games_score`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_games_title`.execute(db);
}
