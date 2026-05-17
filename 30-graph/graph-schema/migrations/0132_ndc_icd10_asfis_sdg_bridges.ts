import { Kysely, sql } from 'kysely';

/**
 * Migration 0132: NDC↔ICD-10 bridge + ASFIS↔SDG + NDC historical ISIC chains.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 54).
 *
 * ## Systems Built
 *
 * ### NDC ↔ ICD-10 (FDA drugs ↔ WHO diseases)
 * | system    | edges | pivot chain                  |
 * |-----------|-------|------------------------------|
 * | ndc_icd10 |     0 | ndc_atc × atc_icd10 = 0      |
 * | icd10_ndc |     0 | reverse = 0                  |
 *
 * NOTE: ndc_atc × atc_icd10 = 0. ndc_atc.dst_vid = ATC at level L5 (5-char chemical
 * substance codes e.g. "A01AA01"). atc_icd10.src_vid = ATC at L1 (1-char therapeutic
 * group codes e.g. "A"). These are DIFFERENT vertex IDs — no chain JOIN match.
 * For drug→disease semantics, a direct ATC-L5→ICD10 concordance table would be needed.
 *
 * ### ASFIS ↔ SDG (fishing species → sustainable development goals)
 * | system   | edges | pivot chain                  |
 * |----------|-------|------------------------------|
 * | asfis_sdg |    96 | asfis_isic4 × isic4_sdg      |
 * | sdg_asfis |    96 | reverse                      |
 *
 * FAO fishing species groups (ISSCAAP) → ISIC4 fishing activities → SDG 14 (Life Below Water).
 * asfis_isic4(73) × isic4_sdg(197).
 *
 * ### NDC historical ISIC chains (pharma manufacturing across ISIC versions)
 * | system     | edges | pivot chain                   |
 * |------------|-------|-------------------------------|
 * | ndc_isic31 | 83,560 | ndc_isic4 × isic4_isic31     |
 * | isic31_ndc | 83,560 | reverse                      |
 * | ndc_isic2  | 83,560 | ndc_isic4 × isic4_isic2      |
 * | isic2_ndc  | 83,560 | reverse                      |
 * | ndc_naics  |      0 | ndc_isic4 × isic4_naics = 0  |
 * | ndc_cofog  |      0 | ndc_isic4 × isic4_cofog = 0  |
 * | ndc_isco   |      0 | ndc_isic4 × isic4_isco = 0   |
 *
 * NOTE: 83,560 = 2/3 × 125,340 ndc_isic4 edges. ndc_isic4 inserts ISIC4 at 3 hierarchy
 * levels: 21 (division), 210 (group), 2100 (class). isic4_isic31/isic2 bridges only
 * cover levels 21 and 210 (not 2100), so 2/3 of NDC rows form chains.
 * ndc_naics/cofog/isco = 0: ISIC4 2100 pharma manufacturing ≠ healthcare sectors.
 *
 * DB after 0132: 8,022,346 edges, 629 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    // ASFIS ↔ SDG
    'asfis_sdg',  'sdg_asfis',
    // NDC historical ISIC (ndc_icd10/naics/cofog/isco = 0)
    'ndc_isic31', 'isic31_ndc',
    'ndc_isic2',  'isic2_ndc',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'asfis_sdg',  'sdg_asfis',
    'ndc_isic31', 'isic31_ndc',
    'ndc_isic2',  'isic2_ndc',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
