import { Kysely, sql } from 'kysely';

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Migration 0066: vertex_occupation_bls — BLS OES May 2024 wage/employment table.
 *
 * Stores US Bureau of Labor Statistics Occupational Employment and Wage
 * Statistics (OES) at SOC-level detail. One row per SOC code × survey year.
 *
 * Source: https://www.bls.gov/oes/special.requests/oesm24nat.zip
 * License: US Government public-domain (17 U.S.C. §105)
 * Coverage: ~830 detailed SOC occupations, US national, May 2024.
 *
 * No PII — pure aggregate occupation statistics.
 * Links to vertex_occupation via `isco_code` (SOC→ISCO-08 major mapping).
 *
 * Design: 90-docs/adr/0027-recruit-talent-public-feed-first.md §Phase 1 BLS
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_occupation_bls (
      vertex_id         VARCHAR PRIMARY KEY,
      rkey              VARCHAR,
      repo              VARCHAR,
      label             VARCHAR,
      source            VARCHAR,
      source_license    VARCHAR,
      source_homepage   VARCHAR,
      soc_code          VARCHAR,
      isco_code         VARCHAR,
      occ_title         VARCHAR,
      occ_group         VARCHAR,
      reference_year    VARCHAR,
      tot_emp           DOUBLE PRECISION,
      emp_prse          DOUBLE PRECISION,
      h_mean            DOUBLE PRECISION,
      a_mean            DOUBLE PRECISION,
      h_pct10           DOUBLE PRECISION,
      h_pct25           DOUBLE PRECISION,
      h_pct50           DOUBLE PRECISION,
      h_pct75           DOUBLE PRECISION,
      h_pct90           DOUBLE PRECISION,
      a_pct10           DOUBLE PRECISION,
      a_pct25           DOUBLE PRECISION,
      a_pct50           DOUBLE PRECISION,
      a_pct75           DOUBLE PRECISION,
      a_pct90           DOUBLE PRECISION,
      ingested_at       VARCHAR
    )
  `.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_occupation_bls`.execute(db);
}
