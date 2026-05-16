import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaikei_statutory_report (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      report_type VARCHAR NOT NULL,
      period_from DATE NOT NULL,
      period_to DATE NOT NULL,
      artifact_cid VARCHAR,
      status VARCHAR NOT NULL,
      generated_at TIMESTAMPTZ NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 100,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaikei_moneyforward_parity_run (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      period_from DATE NOT NULL,
      period_to DATE NOT NULL,
      mf_export_cid VARCHAR,
      rw_total DOUBLE PRECISION NOT NULL DEFAULT 0,
      mf_total DOUBLE PRECISION NOT NULL DEFAULT 0,
      diff_amount DOUBLE PRECISION NOT NULL DEFAULT 0,
      status VARCHAR NOT NULL,
      checked_at TIMESTAMPTZ NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 100,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaisya_saas_asset (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      provider VARCHAR NOT NULL,
      asset_type VARCHAR NOT NULL,
      external_id VARCHAR NOT NULL,
      display_name VARCHAR NOT NULL,
      assignee_did VARCHAR,
      metadata_json VARCHAR,
      status VARCHAR NOT NULL DEFAULT 'active',
      observed_at TIMESTAMPTZ NOT NULL,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 100,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_jinji_year_end_adjustment (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      employee_did VARCHAR NOT NULL,
      tax_year INTEGER NOT NULL,
      declaration_hash VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      artifact_cid VARCHAR,
      completed_at TIMESTAMPTZ,
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 300,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_atrecord_jinji_mynumber_vault_ref (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT NOT NULL,
      owner_did VARCHAR NOT NULL,
      employee_did VARCHAR NOT NULL,
      vault_ref_encrypted VARCHAR NOT NULL,
      declaration_hash VARCHAR NOT NULL,
      status VARCHAR NOT NULL DEFAULT 'active',
      created_at TIMESTAMPTZ NOT NULL,
      sensitivity_ord INTEGER DEFAULT 300,
      actor_did VARCHAR DEFAULT 'anon',
      org_did VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_kaikei_report_owner_period ON vertex_kaikei_statutory_report (owner_did, report_type, period_from, period_to)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kaikei_parity_owner_period ON vertex_kaikei_moneyforward_parity_run (owner_did, period_from, period_to)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kaisya_saas_provider ON vertex_kaisya_saas_asset (owner_did, provider, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jinji_nencho_employee ON vertex_atrecord_jinji_year_end_adjustment (owner_did, employee_did, tax_year)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_jinji_mynumber_employee ON vertex_atrecord_jinji_mynumber_vault_ref (owner_did, employee_did, status)`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const table of [
    "vertex_atrecord_jinji_mynumber_vault_ref",
    "vertex_atrecord_jinji_year_end_adjustment",
    "vertex_kaisya_saas_asset",
    "vertex_kaikei_moneyforward_parity_run",
    "vertex_kaikei_statutory_report",
  ]) {
    await sql.raw(`DROP TABLE IF EXISTS ${table}`).execute(db);
  }
}
