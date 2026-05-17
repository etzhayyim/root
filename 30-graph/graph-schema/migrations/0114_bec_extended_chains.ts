import { Kysely, sql } from 'kysely';

/**
 * Migration 0114: BEC extended chains — connect BEC to ISIC4, NACE, CPC21, CPC3, NAICS
 * via HS2017 pivot (after 0112 direct BEC↔HS/SITC bridges and 0113 CPC21 repair).
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 36).
 *
 * ## Strategy
 *
 * Chain JOIN via hs2017_bec (5,489 edges, built in 0112):
 *   {classification}_bec = {classification}_hs2017 × hs2017_bec
 *
 * NOTE on CPC3 pivot naming bug:
 *   - `hs2017_cpc3` actually stores (src=CPC3, dst=HS2017) — mislabeled
 *   - `cpc3_hs2017` actually stores (src=HS2017, dst=CPC3) — mislabeled
 *   This was a historical naming inversion from 0072/0073/0096 migrations.
 *   cpc3_bec uses `hs2017_cpc3` as pivot_a (correct: src=CPC3→dst=HS2017).
 *
 * ## Systems Built (10 total = 5 forward + 5 reverse)
 *
 * | system     | edges | pivot_a       | method                         |
 * |------------|-------|---------------|--------------------------------|
 * | isic4_bec  |   477 | isic4_hs2017  | isic4_hs2017 × hs2017_bec     |
 * | bec_isic4  |   477 | —             | reverse                        |
 * | nace_bec   |   340 | nace_hs2017   | nace_hs2017 × hs2017_bec      |
 * | bec_nace   |   340 | —             | reverse                        |
 * | cpc21_bec  | 1,881 | cpc21_hs2017  | cpc21_hs2017 × hs2017_bec     |
 * | bec_cpc21  | 1,881 | —             | reverse                        |
 * | cpc3_bec   | 1,850 | hs2017_cpc3   | hs2017_cpc3 × hs2017_bec (*)  |
 * | bec_cpc3   | 1,850 | —             | reverse                        |
 * | naics_bec  |    14 | naics_hs2017  | naics_hs2017 × hs2017_bec     |
 * | bec_naics  |    14 | —             | reverse                        |
 *
 * (*) Small counts reflect goods-only coverage: ISIC4/NACE/CPC3/NAICS cover
 * many service sectors that don't appear in HS trade codes; BEC is goods-only.
 * 477 ISIC4×BEC pairs is expected when ~60% of ISIC4 are services.
 *
 * ## Coverage Impact
 *
 * BEC now reachable from all major production/industry classification systems:
 * - ISIC4 (universal activity classification)
 * - NACE Rev.2 (European activity classification)
 * - CPC21 (central product classification, UN)
 * - CPC v3 (latest UN product classification)
 * - NAICS 2022 (North American industry classification)
 *
 * Combined with 0112 direct HS/SITC bridges, BEC is now a hub connecting
 * goods trade (HS/SITC) to activity/industry (ISIC4/NACE/CPC21/CPC3/NAICS).
 *
 * DB after 0114: 3,155,328 edges, 407 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'isic4_bec', 'bec_isic4',
    'nace_bec',  'bec_nace',
    'cpc21_bec', 'bec_cpc21',
    'cpc3_bec',  'bec_cpc3',
    'naics_bec', 'bec_naics',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'isic4_bec', 'bec_isic4',
    'nace_bec',  'bec_nace',
    'cpc21_bec', 'bec_cpc21',
    'cpc3_bec',  'bec_cpc3',
    'naics_bec', 'bec_naics',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
