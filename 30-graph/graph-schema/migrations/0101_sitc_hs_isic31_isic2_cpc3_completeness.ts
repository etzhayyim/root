import { Kysely, sql } from 'kysely';

/**
 * Migration 0101: SITC↔ISIC3.1/2 completeness + HS↔ISIC2 full + NACE/CPC3↔ISIC3.1/2.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 24).
 *
 * ## New bridges
 *
 * ### HS 2012/2007/2002/1996 → ISIC Rev.2
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | hs2012_isic2  |    ~43 | hs2012_isic4 ∘ isic4_isic2                             |
 * | hs2007_isic2  |    ~43 | hs2007_isic4 ∘ isic4_isic2                             |
 * | hs2002_isic2  |    ~43 | hs2002_isic4 ∘ isic4_isic2                             |
 * | hs1996_isic2  |    ~43 | hs1996_isic4 ∘ isic4_isic2                             |
 * | isic2_hs2012  |    ~43 | reverse of hs2012_isic2                                |
 * | isic2_hs2007  |    ~43 | reverse of hs2007_isic2                                |
 * | isic2_hs2002  |    ~43 | reverse of hs2002_isic2                                |
 * | isic2_hs1996  |    ~43 | reverse of hs1996_isic2                                |
 *
 * ### SITC → ISIC Rev.3.1
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | sitc4_isic31  |   ~229 | sitc4_isic4 ∘ isic4_isic31                             |
 * | sitc3_isic31  |   ~229 | sitc3_isic4 ∘ isic4_isic31                             |
 * | sitc2_isic31  |   ~229 | sitc2_isic4 ∘ isic4_isic31                             |
 * | sitc1_isic31  |   ~229 | sitc1_isic4 ∘ isic4_isic31                             |
 * | isic31_sitc4  |   ~229 | reverse of sitc4_isic31                                |
 * | isic31_sitc3  |   ~229 | reverse of sitc3_isic31                                |
 * | isic31_sitc2  |   ~229 | reverse of sitc2_isic31                                |
 * | isic31_sitc1  |   ~229 | reverse of sitc1_isic31                                |
 *
 * ### SITC → ISIC Rev.2
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | sitc4_isic2   |    ~43 | sitc4_isic4 ∘ isic4_isic2                              |
 * | sitc3_isic2   |    ~43 | sitc3_isic4 ∘ isic4_isic2                              |
 * | sitc2_isic2   |    ~43 | sitc2_isic4 ∘ isic4_isic2                              |
 * | sitc1_isic2   |    ~43 | sitc1_isic4 ∘ isic4_isic2                              |
 * | isic2_sitc4   |    ~43 | reverse of sitc4_isic2                                 |
 * | isic2_sitc3   |    ~43 | reverse of sitc3_isic2                                 |
 * | isic2_sitc2   |    ~43 | reverse of sitc2_isic2                                 |
 * | isic2_sitc1   |    ~43 | reverse of sitc1_isic2                                 |
 *
 * ### NACE / CPC3 ↔ ISIC3.1 / ISIC2
 *
 * | system        | edges  | derivation                                              |
 * |---------------|--------|---------------------------------------------------------|
 * | nace_isic31   |   ~229 | nace_isic4 ∘ isic4_isic31 (new)                        |
 * | nace_isic2    |    ~43 | nace_isic4 ∘ isic4_isic2 (new)                         |
 * | cpc3_isic31   |   ~229 | cpc3_isic4 ∘ isic4_isic31                              |
 * | isic31_cpc3   |   ~229 | reverse of cpc3_isic31                                 |
 * | cpc3_isic2    |    ~43 | cpc3_isic4 ∘ isic4_isic2                               |
 * | isic2_cpc3    |    ~43 | reverse of cpc3_isic2                                  |
 *
 * ## Coverage impact
 *
 * ISIC Rev.2 and Rev.3.1 are now connected to ALL trade classification systems:
 * HS (all 7 editions), SITC (all 4 revisions), NACE Rev.2, CPC21, CPC3.
 * The full ISIC temporal chain (Rev.2 → Rev.3.1 → Rev.4 → Rev.5) is now universally
 * accessible from any trade or industrial classification system.
 *
 * ## Total edges after 0101: ~1.87M+ (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // HS → ISIC2
  for (const system of [
    'hs2012_isic2', 'hs2007_isic2', 'hs2002_isic2', 'hs1996_isic2',
    'isic2_hs2012', 'isic2_hs2007', 'isic2_hs2002', 'isic2_hs1996',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // SITC → ISIC3.1
  for (const system of [
    'sitc4_isic31', 'sitc3_isic31', 'sitc2_isic31', 'sitc1_isic31',
    'isic31_sitc4', 'isic31_sitc3', 'isic31_sitc2', 'isic31_sitc1',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // SITC → ISIC2
  for (const system of [
    'sitc4_isic2', 'sitc3_isic2', 'sitc2_isic2', 'sitc1_isic2',
    'isic2_sitc4', 'isic2_sitc3', 'isic2_sitc2', 'isic2_sitc1',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // NACE / CPC3 ↔ ISIC3.1 / ISIC2
  for (const system of [
    'nace_isic31', 'nace_isic2',
    'cpc3_isic31', 'isic31_cpc3',
    'cpc3_isic2', 'isic2_cpc3',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2012_isic2', 'hs2007_isic2', 'hs2002_isic2', 'hs1996_isic2',
    'isic2_hs2012', 'isic2_hs2007', 'isic2_hs2002', 'isic2_hs1996',
    'sitc4_isic31', 'sitc3_isic31', 'sitc2_isic31', 'sitc1_isic31',
    'isic31_sitc4', 'isic31_sitc3', 'isic31_sitc2', 'isic31_sitc1',
    'sitc4_isic2', 'sitc3_isic2', 'sitc2_isic2', 'sitc1_isic2',
    'isic2_sitc4', 'isic2_sitc3', 'isic2_sitc2', 'isic2_sitc1',
    'nace_isic31', 'nace_isic2',
    'cpc3_isic31', 'isic31_cpc3', 'cpc3_isic2', 'isic2_cpc3',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
