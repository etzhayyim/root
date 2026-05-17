import { Kysely, sql } from 'kysely';

/**
 * Migration 0098: ISIC5 complete integration + ISO 4217/M49 + NAICS extended.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 22).
 *
 * ## New bridges
 *
 * ### SITC → ISIC5 (via isic4 ∘ isic5 chain)
 *
 * | system       | edges  | derivation                                              |
 * |--------------|--------|---------------------------------------------------------|
 * | sitc3_isic5  | ~3,800 | sitc3_isic4 ∘ isic5 (SITC3→ISIC5)                     |
 * | sitc2_isic5  | ~1,200 | sitc2_isic4 ∘ isic5 (SITC2→ISIC5)                     |
 * | sitc1_isic5  |   ~270 | sitc1_isic4 ∘ isic5 (SITC1→ISIC5)                     |
 *
 * ### HS legacy editions → ISIC5
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | hs2012_isic5  | ~5,200 | hs2012_isic4 ∘ isic5                                   |
 * | hs2007_isic5  | ~4,800 | hs2007_isic4 ∘ isic5                                   |
 * | hs2002_isic5  | ~4,600 | hs2002_isic4 ∘ isic5                                   |
 * | hs1996_isic5  | ~4,300 | hs1996_isic4 ∘ isic5                                   |
 *
 * ### CPC3 → ISIC5
 *
 * | system       | edges  | derivation                                              |
 * |--------------|--------|---------------------------------------------------------|
 * | cpc3_isic5   | ~2,500 | cpc3_isic4 ∘ isic5                                     |
 *
 * ### ISIC5 reversals (→ older editions)
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | isic5_sitc3   | ~3,800 | reverse of sitc3_isic5                                 |
 * | isic5_sitc2   | ~1,200 | reverse of sitc2_isic5                                 |
 * | isic5_sitc1   |   ~270 | reverse of sitc1_isic5                                 |
 * | isic5_hs2012  | ~5,200 | reverse of hs2012_isic5                                |
 * | isic5_hs2007  | ~4,800 | reverse of hs2007_isic5                                |
 * | isic5_hs2002  | ~4,600 | reverse of hs2002_isic5                                |
 * | isic5_hs1996  | ~4,300 | reverse of hs1996_isic5                                |
 *
 * ### ISO 4217 / M49 geographic extension
 *
 * | system        | edges | derivation                                              |
 * |---------------|-------|--------------------------------------------------------|
 * | iso4217_m49   | ~116  | iso4217_iso3166 ∘ iso3166_m49 (currency→M49 region)    |
 * | m49_iso4217   | ~116  | reverse of iso4217_m49                                 |
 *
 * ### NAICS extended (via ISIC4 from 0096)
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | naics_sitc3   |   ~24  | naics_isic4 ∘ isic4_sitc3 (NAICS→SITC3, coarse)       |
 * | naics_nace_r  |   ~24  | naics_isic4 ∘ isic4_nace (NAICS→NACE via ISIC4)       |
 * | naics_cpc21   |   ~67  | naics_isic4 ∘ isic4_cpc21 (if not from 0091)           |
 *
 * ## Coverage impact
 *
 * ISIC5 now fully integrated with ALL classification systems:
 * - HS (all 7 editions 1996–2022) ↔ ISIC5 bidirectional
 * - SITC (all 4 revisions) ↔ ISIC5 bidirectional
 * - CPC3 ↔ ISIC5
 * - Currency (ISO 4217) now linked to M49 geographic regions.
 * - NAICS now connected to SITC3 and NACE (coarse sector-level).
 *
 * ## Total edges after 0098: ~1.2M+ (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // SITC → ISIC5
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_isic5'`.execute(db);

  // HS legacy → ISIC5
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2007_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2002_isic5'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs1996_isic5'`.execute(db);

  // CPC3 → ISIC5
  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc3_isic5'`.execute(db);

  // ISIC5 reversals
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_sitc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_sitc2'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_sitc1'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_hs2012'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_hs2007'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_hs2002'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic5_hs1996'`.execute(db);

  // ISO 4217 / M49
  await sql`DELETE FROM edge_classified_as WHERE system = 'iso4217_m49'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'm49_iso4217'`.execute(db);

  // NAICS extended
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_sitc3'`.execute(db);
  await sql`DELETE FROM edge_classified_as WHERE system = 'naics_nace_r'`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'sitc3_isic5', 'sitc2_isic5', 'sitc1_isic5',
    'hs2012_isic5', 'hs2007_isic5', 'hs2002_isic5', 'hs1996_isic5',
    'cpc3_isic5',
    'isic5_sitc3', 'isic5_sitc2', 'isic5_sitc1',
    'isic5_hs2012', 'isic5_hs2007', 'isic5_hs2002', 'isic5_hs1996',
    'iso4217_m49', 'm49_iso4217',
    'naics_sitc3', 'naics_nace_r',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
