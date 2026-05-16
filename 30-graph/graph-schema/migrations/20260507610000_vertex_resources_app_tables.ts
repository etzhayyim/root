import { Kysely, sql } from 'kysely';

// ADR-0095 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_resources_resource (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      kind VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_resources_resource_id ON vertex_resources_resource (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_resources_resource_kind ON vertex_resources_resource (kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_resources_resource_status ON vertex_resources_resource (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_resources_allocation (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      resource_id VARCHAR,
      requester_did VARCHAR,
      quantity BIGINT,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_resources_allocation_id ON vertex_resources_allocation (id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_resources_allocation_resource_id ON vertex_resources_allocation (resource_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_resources_allocation_status ON vertex_resources_allocation (status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_resources_allocation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_resources_resource`.execute(db);
}
