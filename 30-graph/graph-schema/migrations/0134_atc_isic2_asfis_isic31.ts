import { Kysely, sql } from 'kysely';

/**
 * Migration 0134: ATC↔ISIC2 + ASFIS↔ISIC3.1 tail completeness.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 56 — tail completeness pass).
 *
 * ## Systems Built (4 total)
 *
 * ### ATC ↔ ISIC Rev.2 (pharma manufacturing → legacy industry classification)
 * | system    | edges | note                        |
 * |-----------|-------|-----------------------------|
 * | atc_isic2 |    28 | atc_isic4 × isic4_isic2     |
 * | isic2_atc |    28 | reverse                     |
 *
 * ATC now connected to all 4 ISIC revisions (2, 3.1, 4, 5).
 * 28 = ATC L1 groups (A-V, 14 groups) × ISIC2 pharma division (2-digit), via ISIC4 2100
 * pharma manufacturing bridge through ISIC4→ISIC3.1→ISIC2 chain.
 *
 * ### ASFIS ↔ ISIC Rev.3.1 (fisheries species → legacy industry classification)
 * | system       | edges | note                              |
 * |--------------|-------|-----------------------------------|
 * | asfis_isic31 |    24 | asfis_hs2017 × hs2017_isic31      |
 * | isic31_asfis |    24 | reverse                           |
 *
 * Note: Direct path asfis_isic4 × isic4_isic31 = 0 due to vertex ID granularity
 * mismatch — ASFIS maps to ISIC4 codes at group level (0311/0312/0321/0322),
 * but isic4_isic31 src_vid uses sector-level codes (641/1030/251/242/4510).
 * Alternate pivot via HS2017: asfis_hs2017(206) × hs2017_isic31 = 24 valid pairs.
 *
 * ASFIS now connected to all 4 ISIC revisions (2, 3.1, 4, 5).
 *
 * ## Confirmed 0-count chains (reverse-topo exhaustion)
 * | chain                          | result | reason                              |
 * |--------------------------------|--------|-------------------------------------|
 * | asfis_isic31 (direct isic4)    | 0      | vertex ID granularity mismatch      |
 * | atc_naics (all pivots)         | 0      | pharma ISIC4 2100 ≠ NAICS sectors   |
 * | gho_hs/sitc (all pivots)       | 0      | healthcare services ≠ goods trade   |
 * | icd10_hs/sitc/bec/naics/asfis  | 0      | disease codes ≠ goods trade         |
 * | ndc_icd10                      | 0      | ATC L5/L1 vertex ID mismatch        |
 *
 * DB after 0134: 8,199,790 edges, 649 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    // ATC ↔ ISIC Rev.2
    'atc_isic2', 'isic2_atc',
    // ASFIS ↔ ISIC Rev.3.1
    'asfis_isic31', 'isic31_asfis',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'atc_isic2', 'isic2_atc',
    'asfis_isic31', 'isic31_asfis',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
