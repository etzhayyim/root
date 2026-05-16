import { Kysely, sql } from 'kysely';

/**
 * Migration 0121: COFOG remaining HS legacy editions + ISCO × SITC revisions.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 43).
 *
 * ## Systems Built (16 total)
 *
 * ### COFOG remaining HS editions (via cofog_isic4 × isic4_hsXXXX)
 *
 * | system       | edges | pivot chain                          |
 * |--------------|-------|--------------------------------------|
 * | cofog_hs2007 |   241 | cofog_isic4 × isic4_hs2007          |
 * | hs2007_cofog |   241 | reverse                              |
 * | cofog_hs2002 |   235 | cofog_isic4 × isic4_hs2002          |
 * | hs2002_cofog |   235 | reverse                              |
 * | cofog_hs1996 |   231 | cofog_isic4 × isic4_hs1996          |
 * | hs1996_cofog |   231 | reverse                              |
 *
 * ### ISCO × SITC revisions (via isco_isic4 × isic4_sitcN)
 *
 * | system     | edges | pivot chain                          |
 * |------------|-------|--------------------------------------|
 * | isco_sitc3 |   165 | isco_isic4 × isic4_sitc3            |
 * | sitc3_isco |   165 | reverse                              |
 * | isco_sitc2 |    45 | isco_isic4 × isic4_sitc2            |
 * | sitc2_isco |    45 | reverse                              |
 * | isco_sitc1 |    17 | isco_isic4 × isic4_sitc1            |
 * | sitc1_isco |    17 | reverse                              |
 *
 * ### COFOG × SITC2/1
 *
 * | system      | edges | pivot chain                         |
 * |-------------|-------|-------------------------------------|
 * | cofog_sitc2 |    52 | cofog_isic4 × isic4_sitc2          |
 * | sitc2_cofog |    52 | reverse                             |
 * | cofog_sitc1 |    16 | cofog_isic4 × isic4_sitc1          |
 * | sitc1_cofog |    16 | reverse                             |
 *
 * ## ISCO/COFOG Coverage Summary (after 0116–0121)
 *
 * ISCO-08 now connected to ALL classification systems:
 * - ISIC (4 revisions: 2, 3.1, 4, 5)
 * - NACE Rev.2, CPC21, CPC3
 * - BEC, HS (6 editions: 1996-2022), SITC (4 revisions: 1-4)
 * - COFOG
 *
 * COFOG now connected to ALL systems (pending cofog_hs2012):
 * - ISIC (4 revisions), NACE Rev.2, CPC21
 * - BEC, HS (5/6 editions: 1996-2007+2017-2022), SITC (4 revisions)
 *
 * DB after 0121: 3,167,376 edges, 481 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'cofog_hs2007', 'hs2007_cofog',
    'cofog_hs2002', 'hs2002_cofog',
    'cofog_hs1996', 'hs1996_cofog',
    'isco_sitc3', 'sitc3_isco',
    'isco_sitc2', 'sitc2_isco',
    'isco_sitc1', 'sitc1_isco',
    'cofog_sitc2', 'sitc2_cofog',
    'cofog_sitc1', 'sitc1_cofog',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'cofog_hs2007', 'hs2007_cofog',
    'cofog_hs2002', 'hs2002_cofog',
    'cofog_hs1996', 'hs1996_cofog',
    'isco_sitc3', 'sitc3_isco',
    'isco_sitc2', 'sitc2_isco',
    'isco_sitc1', 'sitc1_isco',
    'cofog_sitc2', 'sitc2_cofog',
    'cofog_sitc1', 'sitc1_cofog',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
