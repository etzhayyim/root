import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // vertex_isin_security — normalised per-ISIN row (US + JP)
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isin_security (
      vertex_id         VARCHAR PRIMARY KEY,
      isin              VARCHAR,
      ticker            VARCHAR,
      cik               VARCHAR,
      figi              VARCHAR,
      composite_figi    VARCHAR,
      share_class_figi  VARCHAR,
      company_name      VARCHAR,
      exchange_code     VARCHAR,
      exchange_mic      VARCHAR,
      market_sector     VARCHAR,
      security_type     VARCHAR,
      security_type2    VARCHAR,
      currency          VARCHAR,
      country_iso2      VARCHAR,
      sic               VARCHAR,
      sic_desc          VARCHAR,
      edinet_code       VARCHAR,
      status            VARCHAR NOT NULL DEFAULT 'active',
      actor_did         VARCHAR NOT NULL,
      org_did           VARCHAR NOT NULL,
      created_at        TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_isin_security_isin
      ON vertex_isin_security (isin)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_isin_security_ticker
      ON vertex_isin_security (ticker)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_isin_security_cik
      ON vertex_isin_security (cik)
  `.execute(db);

  // vertex_isin_filing — EDINET JP filing records per ISIN/company
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_isin_filing (
      vertex_id         VARCHAR PRIMARY KEY,
      ticker            VARCHAR,
      edinet_code       VARCHAR,
      doc_id            VARCHAR,
      doc_type          VARCHAR,
      doc_type_code     VARCHAR,
      period_start      VARCHAR,
      period_end        VARCHAR,
      filing_date       VARCHAR,
      company_name      VARCHAR,
      doc_description   VARCHAR,
      pdf_flag          VARCHAR,
      actor_did         VARCHAR NOT NULL,
      org_did           VARCHAR NOT NULL,
      created_at        TIMESTAMP
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_isin_filing_ticker
      ON vertex_isin_filing (ticker)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_isin_filing_edinet_code
      ON vertex_isin_filing (edinet_code)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_isin_filing`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_isin_security`.execute(db);
}
