import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kiyome_clearance (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      subject_did VARCHAR,
      clearance_type VARCHAR,
      description VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kiyome_clearance_subject ON vertex_kiyome_clearance (subject_did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kiyome_clearance_status ON vertex_kiyome_clearance (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kiyome_audit_log (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      actor_did_ref VARCHAR,
      action VARCHAR,
      resource VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kiyome_audit_log_actor ON vertex_kiyome_audit_log (actor_did_ref)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_kiyome_audit_log`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kiyome_clearance`.execute(db);
}
