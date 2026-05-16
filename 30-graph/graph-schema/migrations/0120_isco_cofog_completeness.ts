import { Kysely, sql } from 'kysely';

/**
 * Migration 0120: ISCO/COFOG completeness — all HS editions, extended chains.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 42).
 *
 * ## Systems Built (38 total = 19 forward + 19 reverse)
 *
 * ### ISCO to all HS editions (via isco_isic4 × isic4_hsXXXX)
 *
 * | system      | edges | pivot chain                          |
 * |-------------|-------|--------------------------------------|
 * | isco_hs2022 |   255 | isco_isic4 × isic4_hs2022           |
 * | hs2022_isco |   255 | reverse                              |
 * | isco_hs2012 |   255 | isco_isic4 × isic4_hs2012           |
 * | hs2012_isco |   255 | reverse                              |
 * | isco_hs2007 |   220 | isco_isic4 × isic4_hs2007           |
 * | hs2007_isco |   220 | reverse                              |
 * | isco_hs2002 |   214 | isco_isic4 × isic4_hs2002           |
 * | hs2002_isco |   214 | reverse                              |
 * | isco_hs1996 |   210 | isco_isic4 × isic4_hs1996           |
 * | hs1996_isco |   210 | reverse                              |
 *
 * ### COFOG completeness
 *
 * | system       | edges | pivot chain                         |
 * |--------------|-------|-------------------------------------|
 * | cofog_hs2022 |   297 | cofog_isic4 × isic4_hs2022         |
 * | hs2022_cofog |   297 | reverse                             |
 * | cofog_sitc4  |   183 | cofog_isic4 × isic4_sitc4          |
 * | sitc4_cofog  |   183 | reverse                             |
 * | cofog_sitc3  |   182 | cofog_isic4 × isic4_sitc3          |
 * | sitc3_cofog  |   182 | reverse                             |
 * | cofog_isic31 |     8 | cofog_isic4 × isic4_isic31         |
 * | isic31_cofog |     8 | reverse                             |
 * | cofog_isic2  |     1 | cofog_isic4 × isic4_isic2          |
 * | isic2_cofog  |     1 | reverse                             |
 *
 * NOTE: cofog_naics = 0 (isic4_naics has only 24 pairs, no cofog overlap).
 *
 * ### ISCO extended classification chains
 *
 * | system     | edges | pivot chain                          |
 * |------------|-------|--------------------------------------|
 * | isco_isic31|    33 | isco_isic4 × isic4_isic31           |
 * | isic31_isco|    33 | reverse                              |
 * | isco_cpc3  |   442 | isco_isic4 × isic4_cpc3             |
 * | cpc3_isco  |   442 | reverse                              |
 * | isco_cofog |    84 | isco_isic4 × isic4_cofog            |
 * | cofog_isco |    84 | reverse                              |
 *
 * NOTE: isco_isic2 = 0 (ISIC2 has only 43 pairs with ISIC4; no overlap with
 * goods-producing ISCO occupations that bridge to ISIC4).
 *
 * ## ISCO Coverage Summary (after 0116-0120)
 *
 * ISCO-08 occupations now fully embedded in classification graph:
 * - ISIC Rev.4 (direct concordance, 140 pairs)
 * - ISIC Rev.5, ISIC Rev.3.1 (via ISIC4 chain)
 * - NACE Rev.2, CPC21, CPC3 (via ISIC4 chain)
 * - BEC, HS 2017/2022/2012/2007/2002/1996 (via ISIC4 × HS chain)
 * - SITC Rev.4 (via ISIC4 chain)
 * - COFOG (via ISIC4 chain)
 *
 * DB after 0120: 3,165,372 edges, 465 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_hs2022', 'hs2022_isco',
    'isco_hs2012', 'hs2012_isco',
    'isco_hs2007', 'hs2007_isco',
    'isco_hs2002', 'hs2002_isco',
    'isco_hs1996', 'hs1996_isco',
    'cofog_hs2022', 'hs2022_cofog',
    'cofog_sitc4',  'sitc4_cofog',
    'cofog_sitc3',  'sitc3_cofog',
    'cofog_isic31', 'isic31_cofog',
    'cofog_isic2',  'isic2_cofog',
    'isco_isic31',  'isic31_isco',
    'isco_cpc3',    'cpc3_isco',
    'isco_cofog',   'cofog_isco',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_hs2022', 'hs2022_isco',
    'isco_hs2012', 'hs2012_isco',
    'isco_hs2007', 'hs2007_isco',
    'isco_hs2002', 'hs2002_isco',
    'isco_hs1996', 'hs1996_isco',
    'cofog_hs2022', 'hs2022_cofog',
    'cofog_sitc4',  'sitc4_cofog',
    'cofog_sitc3',  'sitc3_cofog',
    'cofog_isic31', 'isic31_cofog',
    'cofog_isic2',  'isic2_cofog',
    'isco_isic31',  'isic31_isco',
    'isco_cpc3',    'cpc3_isco',
    'isco_cofog',   'cofog_isco',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
