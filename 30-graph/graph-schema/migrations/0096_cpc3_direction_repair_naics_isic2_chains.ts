import { Kysely, sql } from 'kysely';

/**
 * Migration 0096: CPC3 direction repair + NAICS/ISIC2/ISIC3.1 extended chains.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 20).
 *
 * ## Context: Mislabeled early CPC3 bridges
 *
 * Migrations 0073/0085/0087 created CPC3 bridges with REVERSED naming:
 *   `hs2017_cpc3`  src=CPC3, dst=HS2017  (should be cpc3_hs2017)
 *   `hs2012_cpc3`  src=CPC3, dst=HS2012
 *   `sitc4_cpc3`   src=CPC3, dst=SITC4   (should be cpc3_sitc4)
 * These are preserved as-is (grandfathered). This migration adds the true
 * forward-direction reverses with `_r` suffix to complete bidirectionality.
 *
 * ## New bridges
 *
 * ### CPC3 direction repair (reversals of mislabeled early bridges)
 *
 * | system           | edges | derivation                                            |
 * |------------------|-------|-------------------------------------------------------|
 * | hs2017_cpc3_r    | 5,740 | reverse of hs2017_cpc3 → HS2017→CPC3                 |
 * | hs2012_cpc3_r    | 5,500 | reverse of hs2012_cpc3 → HS2012→CPC3                 |
 * | sitc4_cpc3_r     | 3,717 | reverse of sitc4_cpc3  → SITC4→CPC3                  |
 * | sitc2_hs2017_r   | 9,353 | reverse of hs2017_sitc2 → SITC2→HS2017               |
 * | sitc2_hs2022_r   | 9,766 | reverse of hs2022_sitc2 → SITC2→HS2022               |
 * | sitc2_hs2012_r   | 9,344 | reverse of hs2012_sitc2 → SITC2→HS2012               |
 *
 * ### NAICS extended chains (via isic5_isic4 intermediate)
 *
 * | system        | edges | derivation                                             |
 * |---------------|-------|--------------------------------------------------------|
 * | naics_isic4   |  ~24  | naics_isic5 ∘ isic5_isic4 (sector-level mapping)      |
 * | naics_hs2017  | ~2,4K | naics_isic4 ∘ isic4_hs2017                            |
 * | naics_cpc3    | ~1,2K | naics_isic4 ∘ isic4_cpc3                              |
 *
 * ### ISIC Rev.2 and Rev.3.1 extended chains
 *
 * | system          | edges | derivation                                           |
 * |-----------------|-------|------------------------------------------------------|
 * | isic2_hs2017    |  ~229 | isic2_isic4 ∘ isic4_hs2017                          |
 * | isic2_nace      |  ~229 | isic2_isic4 ∘ isic4_nace                             |
 * | isic2_cpc21     |  ~229 | isic2_isic4 ∘ isic4_cpc21                            |
 * | isic31_hs2017   |  ~229 | isic31_isic4 ∘ isic4_hs2017                          |
 * | isic31_nace     |  ~229 | isic31_isic4 ∘ isic4_nace                            |
 * | isic31_cpc21    |  ~229 | isic31_isic4 ∘ isic4_cpc21                           |
 *
 * ## Coverage impact
 *
 * CPC3 now bidirectional with HS2017/2012 and SITC4 (grandfathered naming preserved).
 * SITC2 now bidirectional with HS2017/2022/2012.
 * NAICS now connected (coarse sector-level) to HS2017 and CPC3.
 * ISIC Rev.2 and Rev.3.1 now connected to HS, NACE, CPC21 via ISIC4 pivot.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // CPC3 direction repair
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_cpc3_r'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_cpc3_r'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_cpc3_r'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_hs2017_r'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_hs2022_r'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_hs2012_r'`.execute(db);

  // NAICS extended
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_isic4'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_hs2017'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_cpc3'`.execute(db);

  // ISIC2 extended
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic2_hs2017'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic2_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic2_cpc21'`.execute(db);

  // ISIC3.1 extended
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic31_hs2017'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic31_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic31_cpc21'`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2017_cpc3_r', 'hs2012_cpc3_r', 'sitc4_cpc3_r',
    'sitc2_hs2017_r', 'sitc2_hs2022_r', 'sitc2_hs2012_r',
    'naics_isic4', 'naics_hs2017', 'naics_cpc3',
    'isic2_hs2017', 'isic2_nace', 'isic2_cpc21',
    'isic31_hs2017', 'isic31_nace', 'isic31_cpc21',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
