import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 0043: vertex_talent_cohort table for talent.gftd.ai (ADR-0018 Tier 3 cohort-first).
 *
 * Stores aggregate employment-by-occupation statistics from ILOSTAT
 * (ILO Modelled Estimates, CC-BY-4.0) and other public stat sources
 * (Eurostat, BLS, etc.). NO individual PII — pure cohort counts per
 * (ISCO code, country, sex, time period).
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_talent_cohort (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      label             VARCHAR,
      source            VARCHAR,
      source_license    VARCHAR,
      source_homepage   VARCHAR,
      isco_code         VARCHAR,
      country           VARCHAR,
      sex               VARCHAR,
      time_period       VARCHAR,
      size_thousands    DOUBLE PRECISION,
      unit              VARCHAR,
      ingested_at       VARCHAR,
      props             VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_talent_cohort`.execute(db);
}
