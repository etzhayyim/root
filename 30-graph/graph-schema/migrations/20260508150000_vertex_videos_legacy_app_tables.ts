import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_videos_legacy_video (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      channel_id VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_videos_legacy_video_channel_id ON vertex_videos_legacy_video (channel_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_videos_legacy_video_status ON vertex_videos_legacy_video (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_videos_legacy_channel (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_videos_legacy_channel_status ON vertex_videos_legacy_channel (status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_videos_legacy_channel`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_videos_legacy_video`.execute(db);
}
