import { Kysely, sql } from 'kysely';

/**
 * Migration 0130: GHO repair + ICD-10↔SDG + NDC extended chains + ATC/GHO↔SDG.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 52).
 *
 * ## Systems Built (24 total)
 *
 * ### GHO repairs (systems lost to FLUSH crash in 0129)
 * | system      | edges  | note                                           |
 * |-------------|--------|------------------------------------------------|
 * | isic4_gho   | 45,855 | repair: 0→45,855 (reverse of gho_isic4)        |
 * | cpc21_gho   | 58,083 | repair: 18,000→58,083 (reverse of gho_cpc21)   |
 *
 * ### GHO remaining extended chains (killed before reaching these in 0129 repair)
 * | system    | edges  | pivot chain                        |
 * |-----------|--------|------------------------------------|
 * | gho_cpc3  | 58,083 | gho_isic4 × isic4_cpc3             |
 * | cpc3_gho  | 58,083 | reverse                            |
 * | gho_isco  | 55,026 | gho_isic4 × isic4_isco             |
 * | isco_gho  | 55,026 | reverse                            |
 * | gho_cofog | 12,228 | gho_isic4 × isic4_cofog            |
 * | cofog_gho | 12,228 | reverse                            |
 *
 * NOTE: gho_icd10 / icd10_gho deliberately NOT built.
 * Chain gho_isic4 × isic4_icd10 = 3,057 × 18,463 = 56.4M Cartesian product
 * (every GHO health indicator ↔ every ICD-10 disease code = semantic noise).
 *
 * ### ICD-10 ↔ SDG
 * | system    | edges  | pivot chain                        |
 * |-----------|--------|------------------------------------|
 * | icd10_sdg | 18,802 | icd10_isic4 × isic4_sdg            |
 * | sdg_icd10 | 18,802 | reverse                            |
 *
 * Healthcare ISIC4 codes (86/87/88) → SDG 3 (Good Health) and adjacent goals.
 * 18,463 ICD-10 disease codes now connect to SDG development goals.
 *
 * ### NDC extended chains (via ndc_isic4 × isic4_X)
 * | system    | edges   | note                                      |
 * |-----------|---------|-------------------------------------------|
 * | ndc_isic5 | 125,340 | FDA drugs → ISIC5 pharma (1-to-1 via 2100)|
 * | isic5_ndc | 125,340 | reverse                                    |
 * | ndc_nace  |  41,780 | FDA drugs → NACE C21 pharma               |
 * | nace_ndc  |  41,780 | reverse                                    |
 * | ndc_cpc21 | 334,240 | FDA drugs → CPC21 products (fan-out)       |
 * | cpc21_ndc | 334,240 | reverse                                    |
 * | ndc_cpc3  | 292,460 | FDA drugs → CPC3 service codes             |
 * | cpc3_ndc  | 292,460 | reverse                                    |
 * | ndc_sdg   |  83,560 | FDA drugs → SDG 3 goals                   |
 * | sdg_ndc   |  83,560 | reverse                                    |
 *
 * ndc_isco/cofog/hs/sitc/bec/asfis/icd10 = 0 (NDC only maps to ISIC4 2100
 * pharma manufacturing, which shares no sector codes with healthcare/trade
 * systems).
 *
 * ### ATC ↔ SDG
 * | system  | edges | note                              |
 * |---------|-------|-----------------------------------|
 * | atc_sdg |    28 | atc_isic4 × isic4_sdg             |
 * | sdg_atc |    28 | reverse                           |
 *
 * ### GHO ↔ SDG
 * | system  | edges | note                              |
 * |---------|-------|-----------------------------------|
 * | gho_sdg | 6,114 | gho_isic4 × isic4_sdg             |
 * | sdg_gho | 6,114 | reverse                           |
 *
 * NOTE: gho_atc / atc_gho = 0. Chain gho_isic4 × isic4_atc has no matching
 * ISIC4 codes: gho_isic4 dst = ISIC4 86/87/88 (healthcare), isic4_atc src =
 * ISIC4 2100 (pharma) — no overlap.
 *
 * ## Cluster stability note
 *
 * Added `SET statement_timeout = '90s'` before FLUSH to prevent indefinite
 * blocking (previously caused 21+ min hangs when S3 Hummock checkpoint stalled).
 * icd10_sdg lost rows once (cluster reset during FLUSH attempt 1); rebuilt on
 * retry. All other systems committed cleanly on FLUSH attempt 1.
 *
 * DB after 0130: 7,687,392 edges, 615 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    // GHO repairs
    'isic4_gho',   'cpc21_gho',
    // GHO extended chains
    'gho_cpc3',    'cpc3_gho',
    'gho_isco',    'isco_gho',
    'gho_cofog',   'cofog_gho',
    // ICD-10 ↔ SDG
    'icd10_sdg',   'sdg_icd10',
    // NDC extended
    'ndc_isic5',   'isic5_ndc',
    'ndc_nace',    'nace_ndc',
    'ndc_cpc21',   'cpc21_ndc',
    'ndc_cpc3',    'cpc3_ndc',
    'ndc_sdg',     'sdg_ndc',
    // ATC ↔ SDG
    'atc_sdg',     'sdg_atc',
    // GHO ↔ SDG
    'gho_sdg',     'sdg_gho',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'isic4_gho',   'cpc21_gho',
    'gho_cpc3',    'cpc3_gho',
    'gho_isco',    'isco_gho',
    'gho_cofog',   'cofog_gho',
    'icd10_sdg',   'sdg_icd10',
    'ndc_isic5',   'isic5_ndc',
    'ndc_nace',    'nace_ndc',
    'ndc_cpc21',   'cpc21_ndc',
    'ndc_cpc3',    'cpc3_ndc',
    'ndc_sdg',     'sdg_ndc',
    'atc_sdg',     'sdg_atc',
    'gho_sdg',     'sdg_gho',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
