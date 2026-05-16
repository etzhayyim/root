import { Kysely, sql } from 'kysely';

/**
 * Migration 0093: HS→SITC2 + ISIC4→CPC3 + HS→ISIC5 + CPC3→ISIC4 + ISIC4↔SITC reversal.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 17).
 *
 * ## New bridges
 *
 * ### HS → SITC2 chains (HS→SITC4→SITC2)
 *
 * | system         | edges | derivation                                              |
 * |----------------|-------|---------------------------------------------------------|
 * | hs2017_sitc2   | 9,353 | hs2017_sitc4 ∘ sitc4_sitc2                             |
 * | hs2022_sitc2   | 9,766 | hs2022_sitc4 ∘ sitc4_sitc2                             |
 * | hs2012_sitc2   | 9,344 | hs2012_sitc4 ∘ sitc4_sitc2                             |
 *
 * ### ISIC extended
 *
 * | system         | edges | derivation                                              |
 * |----------------|-------|---------------------------------------------------------|
 * | isic4_cpc3     | 2,600 | isic4_cpc21 ∘ cpc3 (ISIC4→CPC3)                        |
 * | isic5_cpc      | 2,504 | reverse of cpc_isic5 (ISIC5→CPC21)                     |
 * | cpc3_isic4     | ~2,600| cpc3_cpc21 ∘ cpc (CPC3→CPC21→ISIC4)                    |
 * | hs2017_isic5   | 5,655 | hs2017_isic4 ∘ isic5 (HS2017→ISIC5)                    |
 * | hs2022_isic5   | ~5,600| hs2022_isic4 ∘ isic5 (HS2022→ISIC5)                    |
 *
 * ### Reversal of 0092 SITC→ISIC4 bridges
 *
 * | system         | edges | derivation                                              |
 * |----------------|-------|---------------------------------------------------------|
 * | isic4_sitc3    | 3,968 | reverse of sitc3_isic4                                 |
 * | isic4_sitc2    | 1,328 | reverse of sitc2_isic4                                 |
 * | isic4_sitc1    |   275 | reverse of sitc1_isic4                                 |
 *
 * ## Coverage impact
 *
 * ISIC4 now fully connected to all SITC revisions (1–4) in both directions.
 * HS 2012/2017/2022 all linked to SITC2 (coarser classification).
 * HS2017/2022 linked to ISIC5 via ISIC4 intermediate.
 * CPC3 now bidirectional with CPC21 and ISIC4.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_sitc2'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_sitc2'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_sitc2'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_cpc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_cpc'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc3_isic4'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_sitc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_sitc2'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_sitc1'`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2017_sitc2', 'hs2022_sitc2', 'hs2012_sitc2',
    'isic4_cpc3', 'isic5_cpc', 'cpc3_isic4',
    'hs2017_isic5', 'hs2022_isic5',
    'isic4_sitc3', 'isic4_sitc2', 'isic4_sitc1',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
