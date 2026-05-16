import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_manga_title (
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
      series_id VARCHAR,
      user_id VARCHAR,
      title VARCHAR,
      description VARCHAR,
      genre VARCHAR,
      thumbnail_key VARCHAR,
      coin_price BIGINT,
      wait_free_hours BIGINT,
      tags VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manga_title_user_id ON vertex_manga_title (user_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manga_title_genre ON vertex_manga_title (genre)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manga_title_status ON vertex_manga_title (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_manga_chapter (
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
      user_id VARCHAR,
      chapter_num BIGINT,
      episode_title VARCHAR,
      asset_manifest_uri VARCHAR,
      page_count BIGINT,
      published_at VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manga_chapter_title_id ON vertex_manga_chapter (title_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manga_chapter_title_num ON vertex_manga_chapter (title_id, chapter_num)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manga_chapter_status ON vertex_manga_chapter (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_manga_reading_progress (
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
      user_id VARCHAR,
      title_id VARCHAR,
      chapter_id VARCHAR,
      page_num BIGINT,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_manga_progress_user_title ON vertex_manga_reading_progress (user_id, title_id)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_manga_reading_progress`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_manga_chapter`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_manga_title`.execute(db);
}
