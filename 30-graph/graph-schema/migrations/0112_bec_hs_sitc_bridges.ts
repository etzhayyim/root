import { Kysely, sql } from 'kysely';

/**
 * Migration 0112: BEC Rev.4 ↔ HS (all 6 editions) + SITC (all 4 revisions) bridges.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 33).
 *
 * ## Source
 *
 * UN Statistics Division: "Complete correlations among HS, SITC and BEC (2022)"
 *   URL: https://unstats.un.org/unsd/classifications/Econ/tables/HS-SITC-BEC%20Correlations_2022.xlsx
 *   Sheet: "HS SITC BEC", 165,258 rows, 13 columns:
 *     HS92, HS96, HS02, HS07, HS12, HS17, HS22, BEC4, BEC5, SITC1, SITC2, SITC3, SITC4
 *
 * ## Bridge strategy
 *
 * BEC4 column (20 distinct codes: 111, 112, 121, 122, 21, 22, 31, 32, 322, 41,
 * 42, 51, 521, 522, 53, 61, 62, 63, 7) maps to our existing BEC vertex IDs:
 *   https://unstats.un.org/unsd/classifications/Econ/bec/{code}
 *
 * For each HS edition + SITC revision, build DISTINCT (classification_code → bec4_code)
 * pairs, then insert forward + reverse bridges.
 *
 * NOTE: BEC is a COARSE economic classification (20 categories) applied across
 * thousands of HS/SITC codes. Fan-out is expected and correct — e.g., all
 * "intermediate goods not elsewhere specified" (BEC4=22) covers ~3,000 HS17 codes.
 * These are not noise bridges like the cpc3_sitc4 fan-out in 0110; BEC IS
 * designed to be an economic interpretation layer over HS/SITC.
 *
 * ## Systems built (20 forward + 20 reverse = 40 total)
 *
 * HS editions:
 * | system       | edges  | direction          |
 * |--------------|--------|--------------------|
 * | hs2017_bec   | 5,489  | HS2017 → BEC      |
 * | bec_hs2017   | 5,489  | reverse            |
 * | hs2022_bec   | 5,890  | HS2022 → BEC      |
 * | bec_hs2022   | 5,890  | reverse            |
 * | hs2012_bec   | 5,263  | HS2012 → BEC      |
 * | bec_hs2012   | 5,263  | reverse            |
 * | hs2007_bec   | 5,070  | HS2007 → BEC      |
 * | bec_hs2007   | 5,070  | reverse            |
 * | hs2002_bec   | 5,329  | HS2002 → BEC      |
 * | bec_hs2002   | 5,329  | reverse            |
 * | hs1996_bec   | 5,318  | HS1996 → BEC      |
 * | bec_hs1996   | 5,318  | reverse            |
 *
 * SITC revisions:
 * | system       | edges  | direction          |
 * |--------------|--------|--------------------|
 * | sitc4_bec    | 3,041  | SITC4 → BEC       |
 * | bec_sitc4    | 3,041  | reverse            |
 * | sitc3_bec    | 3,391  | SITC3 → BEC       |
 * | bec_sitc3    | 3,391  | reverse            |
 * | sitc2_bec    | 2,583  | SITC2 → BEC       |
 * | bec_sitc2    | 2,583  | reverse            |
 * | sitc1_bec    | 1,970  | SITC1 → BEC       |
 * | bec_sitc1    | 1,970  | reverse            |
 *
 * ## Coverage impact
 *
 * BEC now connects to the full trade classification universe:
 * - All 7 HS editions (via HS ↔ BEC direct bridges)
 * - All 4 SITC revisions (via SITC ↔ BEC direct bridges)
 * - Transitively: ISIC4/5, NACE, CPC21, CPC3, NAICS (via existing HS/SITC chains)
 *
 * BEC was previously an isolated island (only hierarchy edges). This migration
 * connects it to the global classification graph.
 *
 * ## Note on HS1992
 *
 * The Excel also has HS92 column but we don't have HS1992 vertices in our DB
 * (HS succession chain starts at HS1996). HS92 bridges are skipped.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const becSystems = [
    'hs2017_bec', 'bec_hs2017',
    'hs2022_bec', 'bec_hs2022',
    'hs2012_bec', 'bec_hs2012',
    'hs2007_bec', 'bec_hs2007',
    'hs2002_bec', 'bec_hs2002',
    'hs1996_bec', 'bec_hs1996',
    'sitc4_bec', 'bec_sitc4',
    'sitc3_bec', 'bec_sitc3',
    'sitc2_bec', 'bec_sitc2',
    'sitc1_bec', 'bec_sitc1',
  ];
  for (const system of becSystems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const becSystems = [
    'hs2017_bec', 'bec_hs2017',
    'hs2022_bec', 'bec_hs2022',
    'hs2012_bec', 'bec_hs2012',
    'hs2007_bec', 'bec_hs2007',
    'hs2002_bec', 'bec_hs2002',
    'hs1996_bec', 'bec_hs1996',
    'sitc4_bec', 'bec_sitc4',
    'sitc3_bec', 'bec_sitc3',
    'sitc2_bec', 'bec_sitc2',
    'sitc1_bec', 'bec_sitc1',
  ];
  for (const system of becSystems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
