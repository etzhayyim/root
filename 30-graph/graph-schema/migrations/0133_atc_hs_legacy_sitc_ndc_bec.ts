import { Kysely, sql } from 'kysely';

/**
 * Migration 0133: ATC HS legacy editions + ATC SITC remaining + NDC BEC.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 55).
 *
 * ## Systems Built (22 total, 4 confirmed 0)
 *
 * ### ATC HS legacy editions (complete ATC ↔ HS coverage all 6 editions)
 * | system      | edges | note                            |
 * |-------------|-------|---------------------------------|
 * | atc_hs2012  | 1,120 | atc_isic4 × isic4_hs2012        |
 * | hs2012_atc  | 1,120 | reverse                         |
 * | atc_hs2007  | 1,092 | atc_isic4 × isic4_hs2007        |
 * | hs2007_atc  | 1,092 | reverse                         |
 * | atc_hs2002  | 1,064 | atc_isic4 × isic4_hs2002        |
 * | hs2002_atc  | 1,064 | reverse                         |
 * | atc_hs1996  |   798 | atc_isic4 × isic4_hs1996        |
 * | hs1996_atc  |   798 | reverse                         |
 *
 * ATC now fully bidirectional with all 6 HS editions (1996–2022).
 * Decreasing counts reflect fewer pharma HS codes per edition (Chapter 30 evolved).
 *
 * ### ATC ↔ SITC remaining revisions
 * | system    | edges | note                          |
 * |-----------|-------|-------------------------------|
 * | atc_sitc3 |   826 | atc_isic4 × isic4_sitc3       |
 * | sitc3_atc |   826 | reverse                       |
 * | atc_sitc2 |   196 | atc_isic4 × isic4_sitc2       |
 * | sitc2_atc |   196 | reverse                       |
 * | atc_sitc1 |    14 | atc_isic4 × isic4_sitc1       |
 * | sitc1_atc |    14 | reverse                       |
 *
 * ATC now connected to all 4 SITC revisions (sitc4=686 from 0125).
 * Diminishing counts (826→196→14) reflect older SITC revisions having fewer
 * pharmaceutical product codes.
 *
 * ### NDC ↔ BEC (pharma manufacturing → end-use goods classification)
 * | system  | edges  | note                          |
 * |---------|--------|-------------------------------|
 * | ndc_bec | 83,560 | ndc_isic4 × isic4_bec         |
 * | bec_ndc | 83,560 | reverse                       |
 *
 * 83,560 = 2/3 × 125,340 ndc_isic4 (ISIC4 div 21 + group 210 bridge to BEC;
 * class 2100 has no BEC concordance). NDC drugs → BEC end-use categories.
 *
 * ### Confirmed 0-count chains
 * | chain                        | result | reason                        |
 * |------------------------------|--------|-------------------------------|
 * | atc_cofog (atc_isic4 × isic4_cofog) | 0 | ISIC4 2100 pharma ≠ 86/87/88 healthcare |
 * | atc_isco (atc_isic4 × isic4_isco)   | 0 | same sector mismatch          |
 * | gho_hs2017 (gho_isic4 × isic4_hs2017) | 0 | healthcare services ≠ goods HS |
 * | gho_sitc4 (gho_isic4 × isic4_sitc4)   | 0 | healthcare services ≠ goods SITC |
 *
 * DB after 0133: 8,199,686 edges, 645 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    // ATC HS legacy editions
    'atc_hs2012', 'hs2012_atc',
    'atc_hs2007', 'hs2007_atc',
    'atc_hs2002', 'hs2002_atc',
    'atc_hs1996', 'hs1996_atc',
    // ATC SITC remaining
    'atc_sitc3',  'sitc3_atc',
    'atc_sitc2',  'sitc2_atc',
    'atc_sitc1',  'sitc1_atc',
    // NDC ↔ BEC
    'ndc_bec',    'bec_ndc',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'atc_hs2012', 'hs2012_atc',
    'atc_hs2007', 'hs2007_atc',
    'atc_hs2002', 'hs2002_atc',
    'atc_hs1996', 'hs1996_atc',
    'atc_sitc3',  'sitc3_atc',
    'atc_sitc2',  'sitc2_atc',
    'atc_sitc1',  'sitc1_atc',
    'ndc_bec',    'bec_ndc',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
