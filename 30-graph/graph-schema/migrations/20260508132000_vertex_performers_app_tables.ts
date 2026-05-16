import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_performers_profile (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      display_name VARCHAR,
      genre VARCHAR,
      bio VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_performers_profile_genre ON vertex_performers_profile (genre)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_performers_profile_status ON vertex_performers_profile (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_performers_profile_actor_did ON vertex_performers_profile (actor_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_performers_booking (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      profile_id VARCHAR,
      event_date VARCHAR,
      venue VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_performers_booking_profile_id ON vertex_performers_booking (profile_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_performers_booking_status ON vertex_performers_booking (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_performers_booking_event_date ON vertex_performers_booking (event_date)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_performers_booking`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_performers_profile`.execute(db);
}
