import { Kysely, sql } from 'kysely';

// ADR-0095 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_videos_video (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      blob_key VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_videos_video_id ON vertex_videos_video (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_videos_video_status ON vertex_videos_video (status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_videos_video`.execute(db);
}
