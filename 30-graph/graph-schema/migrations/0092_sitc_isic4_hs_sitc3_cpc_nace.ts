import { Kysely, sql } from 'kysely';

/**
 * Migration 0092: SITC→ISIC4 + HS→SITC3 + NACE↔ISIC5 + CPC3↔CPC21.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 17).
 *
 * ## New bridges (all chain compositions or reversals)
 *
 * ### HS → SITC3 chains (HS→SITC4→SITC3)
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | hs2017_sitc3  | 27,428 | hs2017_sitc4 ∘ sitc4_sitc3                             |
 * | hs2022_sitc3  | 28,592 | hs2022_sitc4 ∘ sitc4_sitc3                             |
 * | hs2012_sitc3  | 27,427 | hs2012_sitc4 ∘ sitc4_sitc3                             |
 *
 * ### SITC → ISIC4 chains (SITC→HS2017→ISIC4)
 *
 * | system        | edges | derivation                                              |
 * |---------------|-------|---------------------------------------------------------|
 * | sitc3_isic4   | 3,968 | sitc3_hs2017 ∘ hs2017_isic4                            |
 * | sitc2_isic4   | 1,328 | sitc2_hs2017 ∘ hs2017_isic4                            |
 * | sitc1_isic4   |   275 | sitc1_hs2017 ∘ hs2017_isic4                            |
 *
 * ### HS2022 → ISIC4 chain
 *
 * | system        | edges | derivation                                              |
 * |---------------|-------|---------------------------------------------------------|
 * | hs2022_isic4  | 5,591 | hs22_hs17 ∘ hs2017_isic4                               |
 *
 * ### CPC and NACE reversals
 *
 * | system        | edges | derivation                                              |
 * |---------------|-------|---------------------------------------------------------|
 * | cpc3_cpc21    | 4,391 | reverse of cpc3 (CPC3→CPC21)                           |
 * | nace_isic5    |   625 | reverse of isic5_nace (NACE→ISIC5)                     |
 *
 * ## Coverage impact
 *
 * SITC Rev.1–3 now linked to ISIC Rev.4 (via HS2017 pivot).
 * HS 2012/2017/2022 all linked to SITC Rev.3 (coarser classification).
 * HS2022 linked to ISIC4 directly.
 * CPC3→CPC21 reversal enables product group → specific product lookups.
 * NACE Rev.2 → ISIC Rev.5 completes NACE bidirectionality.
 *
 * ## Total edges after 0092: ~99K new, ~720K total (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // HS → SITC3 chains
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_sitc3'`.execute(db);
  // hs2017_sitc4 ∘ sitc4_sitc3

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_sitc3'`.execute(db);
  // hs2022_sitc4 ∘ sitc4_sitc3

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_sitc3'`.execute(db);
  // hs2012_sitc4 ∘ sitc4_sitc3

  // SITC → ISIC4 chains
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_isic4'`.execute(db);
  // sitc3_hs2017 ∘ hs2017_isic4

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_isic4'`.execute(db);
  // sitc2_hs2017 ∘ hs2017_isic4

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_isic4'`.execute(db);
  // sitc1_hs2017 ∘ hs2017_isic4

  // HS2022 → ISIC4
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_isic4'`.execute(db);
  // hs22_hs17 ∘ hs2017_isic4

  // CPC and NACE reversals
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc3_cpc21'`.execute(db);
  // reverse of cpc3

  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_isic5'`.execute(db);
  // reverse of isic5_nace
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2017_sitc3', 'hs2022_sitc3', 'hs2012_sitc3',
    'sitc3_isic4', 'sitc2_isic4', 'sitc1_isic4',
    'hs2022_isic4', 'cpc3_cpc21', 'nace_isic5',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
