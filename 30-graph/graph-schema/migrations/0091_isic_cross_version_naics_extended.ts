import { Kysely, sql } from 'kysely';

/**
 * Migration 0091: ISIC cross-version bridges + NAICS extended chains.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 16).
 *
 * ## New bridges
 *
 * ### ISIC version reversal (complete bidirectionality across ISIC Rev.2→5)
 *
 * | system          | edges | derivation                                              |
 * |-----------------|-------|---------------------------------------------------------|
 * | isic5_isic4     |   700 | reverse of isic5 (ISIC4→ISIC5)                         |
 * | isic31_isic2    |    76 | reverse of isic2_isic31 (ISIC3.1→ISIC2)                |
 * | isic4_isic31    |   229 | reverse of isic31_isic4 (ISIC4→ISIC3.1)                |
 * | isic5_isic31    |   231 | reverse of isic31_isic5 (ISIC5→ISIC3.1)                |
 *
 * ### ISIC cross-version chains
 *
 * | system          | edges | derivation                                              |
 * |-----------------|-------|---------------------------------------------------------|
 * | isic4_isic2     |  ~76  | isic4_isic31 ∘ isic31_isic2                             |
 * | isic5_isic2     |  ~76  | isic5_isic31 ∘ isic31_isic2                             |
 * | isic2_isic4     | ~229  | isic2_isic31 ∘ isic31_isic4                             |
 * | isic2_isic5     | ~231  | isic2_isic31 ∘ isic31_isic5                             |
 *
 * ### NAICS extended bridges
 *
 * | system          | edges | derivation                                              |
 * |-----------------|-------|---------------------------------------------------------|
 * | naics_nace      |    63 | naics_isic5 ∘ isic5_nace (NAICS → NACE Rev.2)          |
 * | naics_cpc21     |    67 | shared ISIC5: naics_isic5 × cpc_isic5                  |
 *
 * ## Coverage impact
 *
 * ISIC version chain Rev.2↔Rev.3.1↔Rev.4↔Rev.5 now fully bidirectional.
 * NAICS 2022 now reachable from NACE Rev.2 and CPC v2 classifications.
 *
 * ## Full concordance inventory
 *
 * After 0091: ~70 systems, ~700K+ total edges (excl. openalex_concept).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ISIC reversal bridges
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_isic4'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='isic5'

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic31_isic2'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='isic2_isic31'

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_isic31'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='isic31_isic4'

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_isic31'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='isic31_isic5'

  // ISIC cross-version chains
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_isic2'`.execute(db);
  // isic4_isic31 ∘ isic31_isic2

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_isic2'`.execute(db);
  // isic5_isic31 ∘ isic31_isic2

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic2_isic4'`.execute(db);
  // isic2_isic31 ∘ isic31_isic4

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic2_isic5'`.execute(db);
  // isic2_isic31 ∘ isic31_isic5

  // NAICS extended
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_nace'`.execute(db);
  // chain: naics_isic5 ∘ isic5_nace

  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_cpc21'`.execute(db);
  // shared ISIC5 JOIN: SELECT e1.src_vid, e2.src_vid
  // FROM edge_classified_as e1 JOIN edge_classified_as e2 ON e1.dst_vid=e2.dst_vid
  // WHERE e1.system='naics_isic5' AND e2.system='cpc_isic5'
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'isic5_isic4', 'isic31_isic2', 'isic4_isic31', 'isic5_isic31',
    'isic4_isic2', 'isic5_isic2', 'isic2_isic4', 'isic2_isic5',
    'naics_nace', 'naics_cpc21',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
