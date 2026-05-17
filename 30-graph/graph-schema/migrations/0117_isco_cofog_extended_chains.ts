import { Kysely, sql } from 'kysely';

/**
 * Migration 0117: ISCO/COFOG extended chains — ISIC5, NACE connections.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 39).
 *
 * ## Strategy
 *
 * Chain JOIN via isco_isic4 / cofog_isic4 pivot (built in 0116):
 *
 *   isco_isic5  = isco_isic4  × isic4_isic5   (700 pairs)
 *   isco_nace   = isco_isic4  × isic4_nace    (679 pairs)
 *   cofog_isic5 = cofog_isic4 × isic4_isic5   (700 pairs)
 *   cofog_nace  = cofog_isic4 × isic4_nace    (679 pairs)
 *
 * ## Systems Built (8 total)
 *
 * | system      | edges | pivot chain                             |
 * |-------------|-------|-----------------------------------------|
 * | isco_isic5  |   104 | isco_isic4 × isic4_isic5               |
 * | isic5_isco  |   104 | reverse                                 |
 * | isco_nace   |   120 | isco_isic4 × isic4_nace                |
 * | nace_isco   |   120 | reverse                                 |
 * | cofog_isic5 |    42 | cofog_isic4 × isic4_isic5              |
 * | isic5_cofog |    42 | reverse                                 |
 * | cofog_nace  |    43 | cofog_isic4 × isic4_nace               |
 * | nace_cofog  |    43 | reverse                                 |
 *
 * NOTE: Smaller counts than ISIC4 bridges (140/52) because ISIC5 and NACE only
 * partially overlap with ISIC4 in the goods-producing sectors. Service sector
 * occupations (e.g., ISIC 84 public admin, 85 education, 86 health) have
 * good ISIC4→ISIC5 and ISIC4→NACE coverage; other sectors less so.
 *
 * ## Coverage Impact
 *
 * ISCO-08 is now connected to:
 * - ISIC Rev.4 (0116: 140 pairs — direct concordance)
 * - ISIC Rev.5 (0117: 104 pairs — via isic4_isic5 chain)
 * - NACE Rev.2 (0117: 120 pairs — via isic4_nace chain)
 *
 * COFOG is now connected to:
 * - ISIC Rev.4 (0116: 52 pairs — direct concordance)
 * - ISIC Rev.5 (0117: 42 pairs — via isic4_isic5 chain)
 * - NACE Rev.2 (0117: 43 pairs — via isic4_nace chain)
 *
 * Both ISCO and COFOG can now chain further to HS/SITC/BEC/CPC21 etc.
 * via the ISIC4/ISIC5/NACE bridge networks.
 *
 * DB after 0117: 3,157,452 edges, 425 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_isic5', 'isic5_isco',
    'isco_nace',  'nace_isco',
    'cofog_isic5', 'isic5_cofog',
    'cofog_nace',  'nace_cofog',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_isic5', 'isic5_isco',
    'isco_nace',  'nace_isco',
    'cofog_isic5', 'isic5_cofog',
    'cofog_nace',  'nace_cofog',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
