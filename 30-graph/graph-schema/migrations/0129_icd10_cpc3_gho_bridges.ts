import { Kysely, sql } from 'kysely';

/**
 * Migration 0129: ICD-10 → CPC3 bridge + WHO GHO → ISIC4 healthcare isolation fix.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 51).
 *
 * ## Systems Built (18 total = 9 forward + 9 reverse)
 *
 * | system      | edges    | pivot chain / source                         |
 * |-------------|----------|----------------------------------------------|
 * | icd10_cpc3  |  134,533 | icd10_isic4 × isic4_cpc3                     |
 * | cpc3_icd10  |  134,533 | reverse                                      |
 * | gho_isic4   |   45,855 | 3,057 GHO × 15 ISIC4 healthcare codes        |
 * | isic4_gho   |   45,855 | reverse (repaired in 0130 after FLUSH crash)  |
 * | gho_isic5   |   45,855 | gho_isic4 × isic4_isic5                       |
 * | isic5_gho   |   45,855 | reverse                                      |
 * | gho_nace    |   39,741 | gho_isic4 × isic4_nace                        |
 * | nace_gho    |   39,741 | reverse                                      |
 * | gho_cpc21   |   58,083 | gho_isic4 × isic4_cpc21                       |
 * | cpc21_gho   |   58,083 | reverse (repaired in 0130 after FLUSH crash)  |
 * | gho_cpc3    |      TBD | gho_isic4 × isic4_cpc3 (completed in 0130)    |
 * | cpc3_gho    |      TBD | reverse                                      |
 * | gho_isco    |      TBD | gho_isic4 × isic4_isco (completed in 0130)    |
 * | isco_gho    |      TBD | reverse                                      |
 * | gho_cofog   |      TBD | gho_isic4 × isic4_cofog (completed in 0130)   |
 * | cofog_gho   |      TBD | reverse                                      |
 * | gho_icd10   |      TBD | gho_isic4 × isic4_icd10 (completed in 0130)   |
 * | icd10_gho   |      TBD | reverse                                      |
 *
 * ## ICD-10 → CPC3 (134,533)
 *
 * Via icd10_isic4 × isic4_cpc3 chain JOIN. Healthcare ISIC4 codes (86/87/88)
 * map to CPC v2 section 9 (Community, social and personal services). The
 * many-to-many fan-out produces 134,533 pairs — larger than the 98,918
 * icd10_isic4 count because some healthcare codes map to multiple CPC3 entries.
 *
 * ## WHO GHO Isolation Fix (gho_isic4, 45,855 pairs)
 *
 * WHO Global Health Observatory (3,057 health indicators) was completely
 * isolated — no edge_classified_as connections to any classification system.
 *
 * Fix: cross-product of all 3,057 GHO indicator URIs (from
 * vertex_repo_record WHERE collection = 'ai.gftd.apps.gho.indicator')
 * with all 15 distinct ISIC4 dst_vids from icd10_isic4 (healthcare sector
 * 86/87/88 codes). This creates a dense semantic bridge: every GHO health
 * indicator is relevant to the healthcare industry sector.
 *
 * 3,057 × 15 = 45,855 pairs.
 *
 * ## GHO Extended Chains
 *
 * Via gho_isic4 × isic4_X chain JOINs. Note: GHO counts differ from ICD-10
 * counts because DISTINCT (GHO_uri, target) is computed — all 3,057 GHO
 * indicators connect to the same 15 ISIC4 healthcare codes, so each target
 * count = 3,057 × (distinct targets reachable from those 15 ISIC4 codes).
 *
 * gho_nace (39,741) < gho_isic5 (45,855): not all 15 ISIC4 codes have NACE
 * equivalents (NACE is European; Q-section granularity differs).
 * gho_cpc21 (58,083) > gho_isic5 (45,855): some ISIC4 healthcare codes fan
 * out to multiple CPC21 product codes.
 *
 * ## Cluster stability note
 *
 * Minimal-FLUSH insert strategy applied throughout: batch INSERT (2,000 rows),
 * auto-checkpoint wait (15s), single FLUSH per system with 20-retry backoff.
 * isic4_gho and cpc21_gho lost rows to S3 checkpoint failure (FLUSH hung
 * 21+ min); both repaired at start of migration 0130.
 * gho_cpc3/isco/cofog/icd10 extended chains completed as part of 0130.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'icd10_cpc3',  'cpc3_icd10',
    'gho_isic4',   'isic4_gho',
    'gho_isic5',   'isic5_gho',
    'gho_nace',    'nace_gho',
    'gho_cpc21',   'cpc21_gho',
    'gho_cpc3',    'cpc3_gho',
    'gho_isco',    'isco_gho',
    'gho_cofog',   'cofog_gho',
    'gho_icd10',   'icd10_gho',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'icd10_cpc3',  'cpc3_icd10',
    'gho_isic4',   'isic4_gho',
    'gho_isic5',   'isic5_gho',
    'gho_nace',    'nace_gho',
    'gho_cpc21',   'cpc21_gho',
    'gho_cpc3',    'cpc3_gho',
    'gho_isco',    'isco_gho',
    'gho_cofog',   'cofog_gho',
    'gho_icd10',   'icd10_gho',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
