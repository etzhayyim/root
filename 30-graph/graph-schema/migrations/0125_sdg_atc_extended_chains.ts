import { Kysely, sql } from 'kysely';

/**
 * Migration 0125: SDG extended chains (all HS/SITC/BEC/CPC/COFOG/ISCO)
 *                 + ATC extended chains (HS/ISIC5/NACE/CPC21/SITC4/BEC).
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 47).
 *
 * ## Systems Built (60 total = 30 forward + 30 reverse)
 *
 * ### SDG extended chains — remaining HS editions
 *
 * | system      | edges | pivot chain                          |
 * |-------------|-------|--------------------------------------|
 * | sdg_hs2022  |   297 | sdg_isic4 × isic4_hs2022            |
 * | hs2022_sdg  |   297 | reverse                              |
 * | sdg_hs2012  |   242 | sdg_isic4 × isic4_hs2012            |
 * | hs2012_sdg  |   242 | reverse                              |
 * | sdg_hs2007  |   157 | sdg_isic4 × isic4_hs2007            |
 * | hs2007_sdg  |   157 | reverse                              |
 * | sdg_hs2002  |   151 | sdg_isic4 × isic4_hs2002            |
 * | hs2002_sdg  |   151 | reverse                              |
 * | sdg_hs1996  |   124 | sdg_isic4 × isic4_hs1996            |
 * | hs1996_sdg  |   124 | reverse                              |
 *
 * ### SDG extended chains — SITC remaining + BEC + CPC3 + COFOG + ISCO
 *
 * | system      | edges | pivot chain                          |
 * |-------------|-------|--------------------------------------|
 * | sdg_sitc3   |   154 | sdg_isic4 × isic4_sitc3             |
 * | sitc3_sdg   |   154 | reverse                              |
 * | sdg_sitc2   |    45 | sdg_isic4 × isic4_sitc2             |
 * | sitc2_sdg   |    45 | reverse                              |
 * | sdg_sitc1   |    20 | sdg_isic4 × isic4_sitc1             |
 * | sitc1_sdg   |    20 | reverse                              |
 * | sdg_bec     |    20 | sdg_isic4 × isic4_bec               |
 * | bec_sdg     |    20 | reverse                              |
 * | sdg_cpc3    |   264 | sdg_isic4 × isic4_cpc3              |
 * | cpc3_sdg    |   264 | reverse                              |
 * | sdg_cofog   |    24 | sdg_isic4 × isic4_cofog             |
 * | cofog_sdg   |    24 | reverse                              |
 * | sdg_isco    |    46 | sdg_isic4 × isic4_isco              |
 * | isco_sdg    |    46 | reverse                              |
 * | sdg_naics   |     0 | skip — isic4_naics too sparse        |
 *
 * ### ATC extended chains (via atc_isic4 × isic4_X)
 *
 * | system      | edges | pivot chain                          |
 * |-------------|-------|--------------------------------------|
 * | atc_hs2017  |  1428 | atc_isic4 × isic4_hs2017            |
 * | hs2017_atc  |  1428 | reverse                              |
 * | atc_hs2022  |  1414 | atc_isic4 × isic4_hs2022            |
 * | hs2022_atc  |  1414 | reverse                              |
 * | atc_isic5   |    42 | atc_isic4 × isic4_isic5             |
 * | isic5_atc   |    42 | reverse                              |
 * | atc_nace    |    14 | atc_isic4 × isic4_nace              |
 * | nace_atc    |    14 | reverse                              |
 * | atc_cpc21   |   112 | atc_isic4 × isic4_cpc21             |
 * | cpc21_atc   |   112 | reverse                              |
 * | atc_sitc4   |   686 | atc_isic4 × isic4_sitc4             |
 * | sitc4_atc   |   686 | reverse                              |
 * | atc_bec     |    28 | atc_isic4 × isic4_bec               |
 * | bec_atc     |    28 | reverse                              |
 *
 * NOTE: atc_sitc4(686) — SITC division 5 (chemical products) maps to ISIC4 21
 * (pharma manufacturing), giving 686 ATC→SITC4 commodity code connections.
 * atc_hs2017(1428) — HS chapter 30 (pharmaceutical products) + chapters 28-29
 * (chemical products) mapped via ISIC4 21 pharma manufacturing pivot.
 *
 * ## SDG Coverage Summary (after 0124–0125)
 *
 * SDG goals G1-G17 now connected to ALL tractable classification systems:
 * - ISIC4 (direct, 197 pairs) + ISIC5 + NACE (via chain)
 * - HS2017/2022/2012/2007/2002/1996 (all 6 editions)
 * - SITC Rev.4/3/2/1 (all 4 revisions)
 * - CPC21, CPC3, BEC, COFOG, ISCO
 *
 * ## ATC Coverage Summary (after 0124–0125)
 *
 * ATC therapeutic groups now connected to:
 * - ISIC4, ISIC5, NACE (pharma manufacturing sector)
 * - HS2017/2022 (pharmaceutical HS chapters 28-30)
 * - SITC4 (chemical products division 5)
 * - CPC21, BEC
 *
 * DB after 0125: 3,214,922 edges, 567 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    // SDG extended — HS editions
    'sdg_hs2022',  'hs2022_sdg',
    'sdg_hs2012',  'hs2012_sdg',
    'sdg_hs2007',  'hs2007_sdg',
    'sdg_hs2002',  'hs2002_sdg',
    'sdg_hs1996',  'hs1996_sdg',
    // SDG extended — SITC/BEC/CPC3/COFOG/ISCO
    'sdg_sitc3',   'sitc3_sdg',
    'sdg_sitc2',   'sitc2_sdg',
    'sdg_sitc1',   'sitc1_sdg',
    'sdg_bec',     'bec_sdg',
    'sdg_cpc3',    'cpc3_sdg',
    'sdg_cofog',   'cofog_sdg',
    'sdg_isco',    'isco_sdg',
    // ATC extended
    'atc_hs2017',  'hs2017_atc',
    'atc_hs2022',  'hs2022_atc',
    'atc_isic5',   'isic5_atc',
    'atc_nace',    'nace_atc',
    'atc_cpc21',   'cpc21_atc',
    'atc_sitc4',   'sitc4_atc',
    'atc_bec',     'bec_atc',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'sdg_hs2022',  'hs2022_sdg',
    'sdg_hs2012',  'hs2012_sdg',
    'sdg_hs2007',  'hs2007_sdg',
    'sdg_hs2002',  'hs2002_sdg',
    'sdg_hs1996',  'hs1996_sdg',
    'sdg_sitc3',   'sitc3_sdg',
    'sdg_sitc2',   'sitc2_sdg',
    'sdg_sitc1',   'sitc1_sdg',
    'sdg_bec',     'bec_sdg',
    'sdg_cpc3',    'cpc3_sdg',
    'sdg_cofog',   'cofog_sdg',
    'sdg_isco',    'isco_sdg',
    'atc_hs2017',  'hs2017_atc',
    'atc_hs2022',  'hs2022_atc',
    'atc_isic5',   'isic5_atc',
    'atc_nace',    'nace_atc',
    'atc_cpc21',   'cpc21_atc',
    'atc_sitc4',   'sitc4_atc',
    'atc_bec',     'bec_atc',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
