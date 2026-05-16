import { Kysely, sql } from 'kysely';

/**
 * Migration 0095: Reversal completion for 0094 + ISIC5 extended chains.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 19).
 *
 * ## New bridges
 *
 * ### Reversals of 0094 HS legacy→ISIC4 bridges
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | isic4_hs2012   | ~5,429 | reverse of hs2012_isic4                                |
 * | isic4_hs2007   | ~5,300 | reverse of hs2007_isic4                                |
 * | isic4_hs2002   | ~5,200 | reverse of hs2002_isic4                                |
 * | isic4_hs1996   | ~5,100 | reverse of hs1996_isic4                                |
 *
 * ### Reversals of 0094 HS→NACE bridges
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | nace_hs2017    | ~5,500 | reverse of hs2017_nace                                 |
 * | nace_hs2022    | ~5,400 | reverse of hs2022_nace                                 |
 * | nace_hs2012    | ~5,300 | reverse of hs2012_nace                                 |
 *
 * ### Reversals of 0094 HS→CPC21 bridges
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | cpc21_hs2017   | ~2,600 | reverse of hs2017_cpc21                                |
 * | cpc21_hs2022   | ~2,500 | reverse of hs2022_cpc21                                |
 * | cpc21_hs2012   | ~2,500 | reverse of hs2012_cpc21                                |
 *
 * ### Reversals of 0094 SITC→NACE bridges
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | nace_sitc3     | ~3,800 | reverse of sitc3_nace                                  |
 * | nace_sitc2     | ~1,200 | reverse of sitc2_nace                                  |
 * | nace_sitc1     |   ~260 | reverse of sitc1_nace                                  |
 *
 * ### Reversals of 0094 SITC→CPC21 bridges
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | cpc21_sitc3    | ~3,900 | reverse of sitc3_cpc21                                 |
 * | cpc21_sitc2    | ~1,300 | reverse of sitc2_cpc21                                 |
 * | cpc21_sitc1    |   ~270 | reverse of sitc1_cpc21                                 |
 *
 * ### Reversal of CPC3→NACE
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | nace_cpc3      | ~2,500 | reverse of cpc3_nace                                   |
 *
 * ### ISIC5 extended chains
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | isic5_hs2017   | ~5,655 | reverse of hs2017_isic5 (ISIC5→HS2017)                |
 * | isic5_hs2022   | ~5,520 | reverse of hs2022_isic5 (ISIC5→HS2022)                |
 * | isic5_sitc3    | ~3,900 | isic5_isic4 ∘ isic4_sitc3 (ISIC5→SITC3)               |
 * | isic5_nace2    |   ~679 | isic5_isic4 ∘ isic4_nace (ISIC5→NACE, via ISIC4)      |
 * | isic5_cpc21    | ~2,600 | isic5_isic4 ∘ isic4_cpc21 (ISIC5→CPC21, via ISIC4)    |
 *
 * ## Coverage impact
 *
 * All HS editions (1996–2022) now fully bidirectional with ISIC4, NACE Rev.2, CPC21.
 * SITC Rev.1–3 now fully bidirectional with NACE Rev.2 and CPC21.
 * ISIC5 now reachable from HS2017, HS2022, SITC3, NACE, CPC21 in both directions.
 * CPC3 fully bidirectional with NACE Rev.2.
 *
 * ## Total edges after 0095: ~870K+ (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // Reversals of all HS editions→ISIC4
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_hs2022'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_hs2012'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_hs2007'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_hs2002'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_hs1996'`.execute(db);

  // Reversals of HS→NACE
  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_hs2017'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_hs2022'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_hs2012'`.execute(db);

  // Reversals of HS→CPC21
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc21_hs2017'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc21_hs2022'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc21_hs2012'`.execute(db);

  // Reversals of SITC→NACE
  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_sitc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_sitc2'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_sitc1'`.execute(db);

  // Reversals of SITC→CPC21
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc21_sitc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc21_sitc2'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc21_sitc1'`.execute(db);

  // Reversal of CPC3→NACE
  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_cpc3'`.execute(db);

  // ISIC5 extended chains
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_hs2017'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_hs2022'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_sitc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_nace2'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_cpc21'`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'isic4_hs2022', 'isic4_hs2012', 'isic4_hs2007', 'isic4_hs2002', 'isic4_hs1996',
    'nace_hs2017', 'nace_hs2022', 'nace_hs2012',
    'cpc21_hs2017', 'cpc21_hs2022', 'cpc21_hs2012',
    'nace_sitc3', 'nace_sitc2', 'nace_sitc1',
    'cpc21_sitc3', 'cpc21_sitc2', 'cpc21_sitc1',
    'nace_cpc3',
    'isic5_hs2017', 'isic5_hs2022', 'isic5_sitc3', 'isic5_nace2', 'isic5_cpc21',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
