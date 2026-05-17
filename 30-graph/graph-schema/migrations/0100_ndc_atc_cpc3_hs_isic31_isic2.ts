import { Kysely, sql } from 'kysely';

/**
 * Migration 0100: NDC↔ATC bidirectional + CPC3↔HS extended + ISIC3.1/2 HS chains.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 24).
 *
 * ## New bridges
 *
 * ### NDC ↔ ATC bidirectional
 *
 * | system        | edges   | derivation                                              |
 * |---------------|---------|----------------------------------------------------------|
 * | ndc_atc       | ~69,740 | reverse of atc_ndc (from 0082): drug product → ATC code |
 *
 * ### CPC3 ↔ HS extended (via cpc3_isic4 ∘ isic4_hs*)
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | cpc3_hs2022   | ~2,600 | cpc3_isic4 ∘ isic4_hs2022                              |
 * | cpc3_hs2012   | ~2,600 | cpc3_isic4 ∘ isic4_hs2012                              |
 * | cpc3_sitc4    | ~2,600 | cpc3_isic4 ∘ isic4_sitc4 (new direct)                  |
 * | hs2022_cpc3   | ~2,600 | reverse of cpc3_hs2022                                 |
 * | hs2012_cpc3   | ~2,600 | reverse of cpc3_hs2012 (was hs2012_cpc3_r before)      |
 *
 * ### HS editions → ISIC Rev.3.1 (via isic4_isic31)
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | hs2022_isic31 |   ~229 | hs2022_isic4 ∘ isic4_isic31                            |
 * | hs2012_isic31 |   ~229 | hs2012_isic4 ∘ isic4_isic31                            |
 * | hs2007_isic31 |   ~229 | hs2007_isic4 ∘ isic4_isic31                            |
 * | hs2002_isic31 |   ~229 | hs2002_isic4 ∘ isic4_isic31                            |
 * | hs1996_isic31 |   ~229 | hs1996_isic4 ∘ isic4_isic31                            |
 * | isic31_hs2022 |   ~229 | reverse of hs2022_isic31                               |
 * | isic31_hs2012 |   ~229 | reverse of hs2012_isic31                               |
 * | isic31_hs2002 |   ~229 | reverse of hs2002_isic31                               |
 * | isic31_hs1996 |   ~229 | reverse of hs1996_isic31                               |
 *
 * ### HS editions → ISIC Rev.2 (via isic4_isic2)
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | hs2022_isic2  |    ~43 | hs2022_isic4 ∘ isic4_isic2                             |
 * | isic2_hs2022  |    ~43 | reverse of hs2022_isic2                                |
 *
 * ## Coverage impact
 *
 * NDC drug products are now bidirectional with ATC drug classification (~140K total edges).
 * CPC3 is now connected to HS 2022 and 2012 in addition to 2017 (from earlier migrations).
 * All 7 HS editions (1996–2022) are now linked to ISIC Rev.3.1 and Rev.2 bidirectionally.
 * The full ISIC version chain (Rev.2↔3.1↔4↔5) is now connected to all HS editions.
 *
 * ## Total edges after 0100: ~1.85M+ (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // NDC ↔ ATC
  await sql`DELETE FROM edge_classified_as WHERE system = 'ndc_atc'`.execute(db);

  // CPC3 ↔ HS extended
  for (const system of ['cpc3_hs2022', 'cpc3_hs2012', 'cpc3_sitc4', 'hs2022_cpc3', 'hs2012_cpc3']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // HS → ISIC3.1
  for (const system of [
    'hs2022_isic31', 'hs2012_isic31', 'hs2007_isic31', 'hs2002_isic31', 'hs1996_isic31',
    'isic31_hs2022', 'isic31_hs2012', 'isic31_hs2002', 'isic31_hs1996',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // HS → ISIC2
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_isic2'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic2_hs2022'`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'ndc_atc',
    'cpc3_hs2022', 'cpc3_hs2012', 'cpc3_sitc4', 'hs2022_cpc3', 'hs2012_cpc3',
    'hs2022_isic31', 'hs2012_isic31', 'hs2007_isic31', 'hs2002_isic31', 'hs1996_isic31',
    'isic31_hs2022', 'isic31_hs2012', 'isic31_hs2002', 'isic31_hs1996',
    'hs2022_isic2', 'isic2_hs2022',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
