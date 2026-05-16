import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_worlds_scene (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      scene_type VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_worlds_scene_scene_type ON vertex_worlds_scene (scene_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_worlds_scene_status ON vertex_worlds_scene (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_worlds_asset (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      asset_type VARCHAR,
      scene_id VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_worlds_asset_scene_id ON vertex_worlds_asset (scene_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_worlds_asset_asset_type ON vertex_worlds_asset (asset_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_worlds_asset_status ON vertex_worlds_asset (status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_worlds_asset`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_worlds_scene`.execute(db);
}
