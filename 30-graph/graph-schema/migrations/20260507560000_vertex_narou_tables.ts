import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_narou_novel (
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
      description VARCHAR,
      genre VARCHAR,
      tags VARCHAR,
      user_id VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_narou_novel_user_id ON vertex_narou_novel (user_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_narou_novel_genre ON vertex_narou_novel (genre)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_narou_novel_status ON vertex_narou_novel (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_narou_chapter (
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
      novel_id VARCHAR,
      chapter_num BIGINT,
      title VARCHAR,
      content VARCHAR,
      word_count BIGINT,
      user_id VARCHAR,
      published_at VARCHAR,
      asset_manifest_uri VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_narou_chapter_novel_id ON vertex_narou_chapter (novel_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_narou_chapter_novel_num ON vertex_narou_chapter (novel_id, chapter_num)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_narou_chapter_status ON vertex_narou_chapter (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_narou_character (
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
      novel_id VARCHAR,
      name VARCHAR,
      role VARCHAR,
      description VARCHAR,
      user_id VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_narou_character_novel_id ON vertex_narou_character (novel_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_narou_world_setting (
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
      novel_id VARCHAR,
      name VARCHAR,
      description VARCHAR,
      user_id VARCHAR,
      org_id VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_narou_world_setting_novel_id ON vertex_narou_world_setting (novel_id)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_narou_world_setting`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_narou_character`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_narou_chapter`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_narou_novel`.execute(db);
}
