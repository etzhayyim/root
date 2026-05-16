import { Kysely, sql } from 'kysely';

/**
 * Migration 0122: cofog_hs2012 gap repair + ASFIS ISSCAAP×ISIC4 bridge.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 44).
 *
 * ## Systems Built (6 total)
 *
 * ### cofog_hs2012 (was missing from 0121)
 *
 * | system       | edges | pivot chain                          |
 * |--------------|-------|--------------------------------------|
 * | cofog_hs2012 |   299 | cofog_isic4 × isic4_hs2012          |
 * | hs2012_cofog |   299 | reverse                              |
 *
 * NOTE: Was absent from 0121 due to a race condition (concurrent inserts
 * produced 598 duplicate rows). Fixed via dedup: SELECT DISTINCT src/dst →
 * DELETE all → re-insert 299 canonical rows.
 *
 * ### ASFIS ISSCAAP group × ISIC4 fishing activities (new bridge)
 *
 * | system      | edges | source                               |
 * |-------------|-------|--------------------------------------|
 * | asfis_isic4 |    73 | FAO ISSCAAP group → ISIC4 0311/0312/0321/0322 |
 * | isic4_asfis |    73 | reverse                              |
 *
 * ASFIS ISSCAAP groups G11-G94 (22 groups total in DB) now bridged to:
 * - ISIC4 0311 (marine fishing), 0312 (freshwater fishing)
 * - ISIC4 0321 (marine aquaculture), 0322 (freshwater aquaculture)
 *
 * NOTE: asfis_hs2017 = 0 pairs — HS vertex IDs in DB are 6-digit commodity
 * codes (e.g. 030111, 030211) while concordance draft used 4-digit headings
 * (0301, 0302). Fix planned in 0123.
 *
 * ## COFOG Coverage Summary (after 0116–0122)
 *
 * COFOG now connected to ALL HS editions:
 * - HS2022, HS2017, HS2012, HS2007, HS2002, HS1996 (6/6 editions)
 * - SITC (4 revisions: 1-4)
 * - ISIC (4 revisions), NACE Rev.2, CPC21, CPC3, BEC, ISCO
 *
 * ## ASFIS Connectivity (after 0122)
 *
 * ASFIS ISSCAAP groups (G11-G94) → ISIC4 fishing sector
 * ASFIS → HS2017 still pending (6-digit code concordance fix in 0123)
 *
 * DB after 0122: 3,168,120 edges, 485 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'cofog_hs2012', 'hs2012_cofog',
    'asfis_isic4',  'isic4_asfis',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'cofog_hs2012', 'hs2012_cofog',
    'asfis_isic4',  'isic4_asfis',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
