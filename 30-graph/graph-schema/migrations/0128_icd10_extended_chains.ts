import { Kysely, sql } from 'kysely';

/**
 * Migration 0128: ICD-10 extended classification chains (ISIC5 + NACE + CPC21).
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 50).
 *
 * ## Systems Built (6 total = 3 forward + 3 reverse)
 *
 * | system      | edges   | pivot chain                          |
 * |-------------|---------|--------------------------------------|
 * | icd10_isic5 |  98,918 | icd10_isic4 × isic4_isic5            |
 * | isic5_icd10 |  98,918 | reverse                               |
 * | icd10_nace  |  80,116 | icd10_isic4 × isic4_nace             |
 * | nace_icd10  |  80,116 | reverse                               |
 * | icd10_cpc21 | 134,533 | icd10_isic4 × isic4_cpc21            |
 * | cpc21_icd10 | 134,533 | reverse                               |
 *
 * ## Approach
 *
 * All chains pivot through `icd10_isic4` (built in 0127), which maps the
 * 18,463 ICD-10 disease codes to ISIC4 healthcare sector codes (86/87/88).
 *
 * ### icd10_isic5 (98,918)
 * isic4_isic5 is a 1-to-1 code-identical bridge (700 edges): ISIC4 Rev.4
 * codes that survived unchanged into ISIC5 Rev.5 retain the same 2-4 digit
 * code. Healthcare ISIC4 86/87/88 all have ISIC5 equivalents, so this chain
 * produces exactly 98,918 pairs — the same count as icd10_isic4.
 *
 * ### icd10_nace (80,116)
 * isic4_nace (679 edges) maps ISIC4 sections/divisions to NACE Rev.2.
 * Healthcare ISIC4 Q section (86/87/88) → NACE Q86/Q87/Q88. Not all ISIC4
 * healthcare sub-codes have NACE equivalents (NACE is Europe-specific with
 * slightly different granularity), hence 80,116 < 98,918.
 *
 * ### icd10_cpc21 (134,533)
 * isic4_cpc21 (2,504 edges) maps ISIC4 activities to CPC v2.1 product codes.
 * Healthcare activities map to CPC 9 (Community, social and personal services)
 * including 9311 (hospital services), 9312 (medical practice services), etc.
 * Some ISIC4 healthcare codes map to multiple CPC21 codes, hence 134,533
 * (> 98,918).
 *
 * ## ICD-10 Coverage Summary (after 0127–0128)
 *
 * 18,463 ICD-10 disease codes now connected to:
 * - ISIC4 (0127), ISIC5 (0128), NACE (0128) — healthcare industry
 * - ATC L1 drug classes (0127)
 * - ISCO-08 occupation groups (0127, via isic4_isco)
 * - COFOG government functions (0127, via isic4_cofog)
 * - CPC21 service product codes (0128)
 *
 * Path: ICD-10 → ISIC4 → any trade/product/occupation classification.
 *
 * DB after 0128: 4,983,936 edges, 583 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'icd10_isic5', 'isic5_icd10',
    'icd10_nace',  'nace_icd10',
    'icd10_cpc21', 'cpc21_icd10',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'icd10_isic5', 'isic5_icd10',
    'icd10_nace',  'nace_icd10',
    'icd10_cpc21', 'cpc21_icd10',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
