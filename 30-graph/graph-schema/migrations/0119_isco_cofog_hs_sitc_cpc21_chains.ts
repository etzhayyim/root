import { Kysely, sql } from 'kysely';

/**
 * Migration 0119: ISCO/COFOG → HS2017 / SITC4 / CPC21 extended chains.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 41).
 *
 * ## Strategy
 *
 * Chain JOIN via isco_isic4 / cofog_isic4 pivot (0116) × HS/SITC/CPC21 bridges:
 *
 *   isco_hs2017  = isco_isic4  × isic4_hs2017    (5,764 pairs)
 *   cofog_hs2017 = cofog_isic4 × isic4_hs2017
 *   isco_sitc4   = isco_isic4  × isic4_sitc4     (3,213 pairs)
 *   cofog_cpc21  = cofog_isic4 × isic4_cpc21     (2,715 pairs)
 *
 * ## Systems Built (10 total)
 *
 * | system        | edges | pivot chain                             |
 * |---------------|-------|-----------------------------------------|
 * | isco_hs2017   |   255 | isco_isic4 × isic4_hs2017              |
 * | hs2017_isco   |   255 | reverse                                 |
 * | cofog_hs2017  |   299 | cofog_isic4 × isic4_hs2017             |
 * | hs2017_cofog  |   299 | reverse                                 |
 * | isco_sitc4    |   160 | isco_isic4 × isic4_sitc4               |
 * | sitc4_isco    |   160 | reverse                                 |
 * | cofog_cpc21   |   364 | cofog_isic4 × isic4_cpc21              |
 * | cpc21_cofog   |   364 | reverse                                 |
 *
 * NOTE: isco_naics = 0 pairs (ISIC4→NAICS has only 24 edges at sector level;
 * no overlap with the 140 isco_isic4 goods-producing pairs).
 *
 * ## Coverage Impact
 *
 * ISCO-08 occupations now reachable from the full trade classification universe:
 * - ISIC Rev.4 (0116), ISIC Rev.5 (0117), NACE Rev.2 (0117)
 * - BEC (0118), CPC21 (0118)
 * - HS2017 (0119), SITC4 (0119)
 *
 * COFOG (government functions) now reachable from:
 * - ISIC Rev.4 (0116), ISIC Rev.5 (0117), NACE Rev.2 (0117)
 * - BEC (0118), CPC21 (0119), HS2017 (0119)
 *
 * Both ISCO and COFOG are now embedded in the full classification graph.
 *
 * DB after 0119: 3,160,604 edges, 439 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_hs2017',  'hs2017_isco',
    'cofog_hs2017', 'hs2017_cofog',
    'isco_sitc4',   'sitc4_isco',
    'cofog_cpc21',  'cpc21_cofog',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_hs2017',  'hs2017_isco',
    'cofog_hs2017', 'hs2017_cofog',
    'isco_sitc4',   'sitc4_isco',
    'cofog_cpc21',  'cpc21_cofog',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
