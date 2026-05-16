import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations — tier: A

export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_sixir_company (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      ticker VARCHAR,
      name VARCHAR,
      exchange VARCHAR,
      sector VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sixir_company_ticker ON vertex_sixir_company (ticker)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sixir_company_exchange ON vertex_sixir_company (exchange)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_sixir_filing (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      company_id VARCHAR,
      filing_type VARCHAR,
      period VARCHAR,
      filed_at VARCHAR,
      summary VARCHAR,
      eps_actual DOUBLE PRECISION,
      eps_estimate DOUBLE PRECISION,
      revenue_actual DOUBLE PRECISION,
      revenue_estimate DOUBLE PRECISION,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sixir_filing_company_id ON vertex_sixir_filing (company_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sixir_filing_type ON vertex_sixir_filing (filing_type)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_sixir_filing_period ON vertex_sixir_filing (period)`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_sixir_filing`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_sixir_company`.execute(db);
}
