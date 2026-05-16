import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ge_org (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      country VARCHAR,
      industry VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ge_org_country ON vertex_ge_org (country)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ge_org_status ON vertex_ge_org (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ge_project (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      org_id VARCHAR,
      name VARCHAR,
      description VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ge_project_org_id ON vertex_ge_project (org_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ge_project_status ON vertex_ge_project (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ge_resource_assignment (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      project_id VARCHAR,
      resource_did VARCHAR,
      role VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ge_resource_project_id ON vertex_ge_resource_assignment (project_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_ge_resource_did ON vertex_ge_resource_assignment (resource_did)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_ge_resource_assignment`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ge_project`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ge_org`.execute(db);
}
