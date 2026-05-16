import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_anime_title (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      title VARCHAR,
      title_ja VARCHAR,
      genre VARCHAR,
      tags VARCHAR,
      synopsis VARCHAR,
      studio VARCHAR,
      source_type VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anime_title_genre ON vertex_anime_title (genre)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anime_title_status ON vertex_anime_title (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_anime_season (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      title_id VARCHAR,
      season_num BIGINT,
      year BIGINT,
      cour VARCHAR,
      episode_count BIGINT,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anime_season_title_id ON vertex_anime_season (title_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_anime_episode (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      season_id VARCHAR,
      episode_num BIGINT,
      title VARCHAR,
      air_date VARCHAR,
      duration_sec BIGINT,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anime_episode_season_id ON vertex_anime_episode (season_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anime_episode_air_date ON vertex_anime_episode (air_date)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_anime_schedule (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      title_id VARCHAR,
      season_id VARCHAR,
      channel VARCHAR,
      day_of_week VARCHAR,
      time_slot VARCHAR,
      start_date VARCHAR,
      end_date VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anime_schedule_title_id ON vertex_anime_schedule (title_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anime_schedule_day ON vertex_anime_schedule (day_of_week)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_anime_review (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      id VARCHAR,
      title_id VARCHAR,
      reviewer_did VARCHAR,
      rating BIGINT,
      body VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_anime_review_title_id ON vertex_anime_review (title_id)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_anime_review`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_anime_schedule`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_anime_episode`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_anime_season`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_anime_title`.execute(db);
}
