import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wvme_scan (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      target VARCHAR,
      scan_type VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wvme_scan_status ON vertex_wvme_scan (status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wvme_scan_target ON vertex_wvme_scan (target)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wvme_vulnerability (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      scan_id VARCHAR,
      cve_id VARCHAR,
      severity VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wvme_vulnerability_scan_id ON vertex_wvme_vulnerability (scan_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wvme_vulnerability_severity ON vertex_wvme_vulnerability (severity)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_wvme_vulnerability_status ON vertex_wvme_vulnerability (status)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_wvme_vulnerability`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_wvme_scan`.execute(db);
}
