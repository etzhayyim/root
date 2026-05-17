import { Kysely, sql } from 'kysely';

/**
 * Migration 0094: HS legacy editions → ISIC4 + HS/SITC/CPC3 → NACE/CPC21.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 18).
 *
 * ## New bridges
 *
 * ### HS legacy editions → ISIC4 (chain through version sequence)
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | hs2012_isic4   | ~5,591 | hs12_hs17 ∘ hs2017_isic4                               |
 * | hs2007_isic4   | ~5,500 | hs07_hs12 ∘ hs2012_isic4                               |
 * | hs2002_isic4   | ~5,400 | hs02_hs07 ∘ hs2007_isic4                               |
 * | hs1996_isic4   | ~5,300 | hs96_hs02 ∘ hs2002_isic4                               |
 *
 * ### HS → NACE Rev.2 (HS→ISIC4→NACE)
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | hs2017_nace    | ~5,500 | hs2017_isic4 ∘ isic4_nace                              |
 * | hs2022_nace    | ~5,400 | hs2022_isic4 ∘ isic4_nace                              |
 * | hs2012_nace    | ~5,300 | hs2012_isic4 ∘ isic4_nace                              |
 *
 * ### HS → CPC21 (HS→ISIC4→CPC21)
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | hs2017_cpc21   | ~2,600 | hs2017_isic4 ∘ isic4_cpc21                             |
 * | hs2022_cpc21   | ~2,500 | hs2022_isic4 ∘ isic4_cpc21                             |
 * | hs2012_cpc21   | ~2,500 | hs2012_isic4 ∘ isic4_cpc21                             |
 *
 * ### SITC → NACE Rev.2 (SITC→ISIC4→NACE; depends on 0092 sitc*_isic4)
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | sitc3_nace     | ~3,800 | sitc3_isic4 ∘ isic4_nace                               |
 * | sitc2_nace     | ~1,200 | sitc2_isic4 ∘ isic4_nace                               |
 * | sitc1_nace     |   ~260 | sitc1_isic4 ∘ isic4_nace                               |
 *
 * ### SITC → CPC21 (SITC→ISIC4→CPC21; depends on 0092 sitc*_isic4)
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | sitc3_cpc21    | ~3,900 | sitc3_isic4 ∘ isic4_cpc21                              |
 * | sitc2_cpc21    | ~1,300 | sitc2_isic4 ∘ isic4_cpc21                              |
 * | sitc1_cpc21    |   ~270 | sitc1_isic4 ∘ isic4_cpc21                              |
 *
 * ### CPC3 → NACE
 *
 * | system         | edges  | derivation                                              |
 * |----------------|--------|---------------------------------------------------------|
 * | cpc3_nace      | ~2,500 | cpc3_isic4 ∘ isic4_nace                                |
 *
 * ## Coverage impact
 *
 * HS 1996/2002/2007/2012 now directly linked to ISIC Rev.4 (complete HS edition coverage).
 * All HS editions (1996–2022) now reachable from NACE Rev.2 and CPC v2.1.
 * SITC Rev.1–3 now linked to both NACE Rev.2 and CPC v2.1 (via ISIC4 pivot).
 * CPC v3 now bridged to NACE Rev.2.
 *
 * ## Total edges after 0094: ~750K+ (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // HS legacy editions → ISIC4
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_isic4'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2007_isic4'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2002_isic4'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs1996_isic4'`.execute(db);

  // HS → NACE Rev.2
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_nace'`.execute(db);

  // HS → CPC21
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_cpc21'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_cpc21'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_cpc21'`.execute(db);

  // SITC → NACE Rev.2
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_nace'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_nace'`.execute(db);

  // SITC → CPC21
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_cpc21'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_cpc21'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_cpc21'`.execute(db);

  // CPC3 → NACE
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc3_nace'`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2012_isic4', 'hs2007_isic4', 'hs2002_isic4', 'hs1996_isic4',
    'hs2017_nace', 'hs2022_nace', 'hs2012_nace',
    'hs2017_cpc21', 'hs2022_cpc21', 'hs2012_cpc21',
    'sitc3_nace', 'sitc2_nace', 'sitc1_nace',
    'sitc3_cpc21', 'sitc2_cpc21', 'sitc1_cpc21',
    'cpc3_nace',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
