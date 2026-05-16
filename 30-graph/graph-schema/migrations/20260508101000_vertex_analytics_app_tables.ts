import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_analytics_dashboard (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      description VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_analytics_dashboard_owner ON vertex_analytics_dashboard (owner_did)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_analytics_event (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      event_name VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_analytics_event_name ON vertex_analytics_event (event_name)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_analytics_event_actor ON vertex_analytics_event (actor_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_analytics_event_created ON vertex_analytics_event (created_at)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_analytics_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_analytics_dashboard`.execute(db);
}
