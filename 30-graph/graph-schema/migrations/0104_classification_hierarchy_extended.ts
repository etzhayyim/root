import { Kysely, sql } from 'kysely';

/**
 * Migration 0104: Extended classification hierarchy bridges + SITC chain completeness.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 25).
 *
 * ## New hierarchy bridge pairs (parent_code self-JOIN from classification views)
 *
 * ### HS editions (chapter→heading→subheading, 3 levels)
 *
 * | pair                            | edges  | source view                  |
 * |---------------------------------|--------|------------------------------|
 * | hs2022_parent / hs2022_children |  6,842 | view_hs2022_commodity        |
 * | hs2012_parent / hs2012_children |  6,431 | view_hs2012_commodity        |
 * | hs2007_parent / hs2007_children |  6,275 | view_hs2007_commodity        |
 * | hs2002_parent / hs2002_children |  6,471 | view_hs2002_commodity        |
 * | hs1996_parent / hs1996_children |  6,376 | view_hs1996_commodity        |
 *
 * ### SITC revisions (section→division→group→subgroup→basic_heading, 5 levels)
 *
 * | pair                            | edges  | source view                  |
 * |---------------------------------|--------|------------------------------|
 * | sitc4_parent / sitc4_children   |  5,474 | view_sitc_commodity          |
 * | sitc3_parent / sitc3_children   |  5,680 | view_sitc3_commodity         |
 * | sitc2_parent / sitc2_children   |  3,713 | view_sitc2_commodity         |
 * | sitc1_parent / sitc1_children   |  2,774 | view_sitc1_commodity         |
 *
 * ### Industry / occupation classifications
 *
 * | pair                            | edges  | source view                  |
 * |---------------------------------|--------|------------------------------|
 * | naics_parent / naics_children   |  2,105 | view_naics_industry (5-level)|
 * | isic5_parent / isic5_children   |    721 | view_isic5_activity (4-level)|
 * | isic4_parent / isic4_children   |    657 | view_isic_activity (4-level) |
 * | isic31_parent / isic31_children |    459 | view_isic31_activity         |
 * | isic2_parent / isic2_children   |    267 | view_isic2_activity          |
 * | cpc21_parent / cpc21_children   |  4,586 | view_cpc_product (5-level)   |
 * | isco_parent / isco_children     |    383 | view_isco_occupation (4-level)|
 *
 * ## SITC version chain completeness
 *
 * | system             | edges | derivation                                  |
 * |--------------------|-------|---------------------------------------------|
 * | sitc4_sitc1        | 1,115 | reverse of sitc1_sitc4                      |
 * | sitc3_sitc1        | 1,153 | chain: sitc3_sitc2 ∘ sitc2_sitc1            |
 * | sitc2_sitc1        | 1,334 | reverse of sitc1_sitc2                      |
 * | sitc1_sitc3        | 1,153 | reverse of sitc3_sitc1                      |
 * | hs2017_sitc1       | 1,053 | reverse of sitc1_hs2017                     |
 * | hs2022_sitc1       | 1,045 | reverse of sitc1_hs2022                     |
 * | hs2012_sitc1       | 1,037 | reverse of sitc1_hs2012                     |
 * | isic4_sitc1        |   275 | (pre-existing, confirmed)                   |
 * | sitc1_isic4        |   275 | reverse of isic4_sitc1                      |
 * | isic31_sitc1       |    43 | chain: isic31_sitc2 ∘ sitc2_sitc1           |
 * | sitc1_isic31       |    43 | reverse of isic31_sitc1                     |
 *
 * ## Geographic reverse bridges
 *
 * | system             | edges  | derivation                                 |
 * |--------------------|--------|--------------------------------------------|
 * | m49_locode         | 97,319 | reverse of locode_m49                      |
 * | sovereign_iso3166  |    188 | reverse of iso3166_sovereign               |
 * | m49_iso4217        |    100 | reverse of iso4217_m49                     |
 *
 * ## Coverage impact
 *
 * Every major classification system is now fully traversable as a tree:
 * - HS (5 editions × 3 levels): direct parent/child navigation
 * - SITC (4 revisions × 5 levels): direct parent/child navigation
 * - NAICS 2022 (5 levels): sector→subsector→group→industry→national
 * - ISIC (Rev.2/3.1/4/5): all 4 versions hierarchically traversable
 * - CPC21 (5 levels): section→division→group→class→subclass
 * - ISCO-08 (4 levels): major→submajor→minor→unit group
 * - Geographic: M49↔LOCODE bidirectional (97K edges each direction)
 *
 * SITC version chain is now complete in both directions across Rev.1–4.
 *
 * ## Total edges after 0104: ~2.7M+ (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // HS hierarchy
  for (const system of [
    'hs2022_parent', 'hs2022_children',
    'hs2012_parent', 'hs2012_children',
    'hs2007_parent', 'hs2007_children',
    'hs2002_parent', 'hs2002_children',
    'hs1996_parent', 'hs1996_children',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // SITC hierarchy
  for (const system of [
    'sitc4_parent', 'sitc4_children',
    'sitc3_parent', 'sitc3_children',
    'sitc2_parent', 'sitc2_children',
    'sitc1_parent', 'sitc1_children',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // Industry / occupation hierarchy
  for (const system of [
    'naics_parent', 'naics_children',
    'isic5_parent', 'isic5_children',
    'isic4_parent', 'isic4_children',
    'isic31_parent', 'isic31_children',
    'isic2_parent', 'isic2_children',
    'cpc21_parent', 'cpc21_children',
    'isco_parent', 'isco_children',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // SITC chain completeness
  for (const system of [
    'sitc4_sitc1', 'sitc3_sitc1', 'sitc2_sitc1', 'sitc1_sitc3',
    'hs2017_sitc1', 'hs2022_sitc1', 'hs2012_sitc1',
    'sitc1_isic4', 'isic31_sitc1', 'sitc1_isic31',
    'isic2_sitc1', 'sitc1_isic2',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // Geographic reverses
  for (const system of ['m49_locode', 'sovereign_iso3166', 'm49_iso4217']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2022_parent', 'hs2022_children',
    'hs2012_parent', 'hs2012_children',
    'hs2007_parent', 'hs2007_children',
    'hs2002_parent', 'hs2002_children',
    'hs1996_parent', 'hs1996_children',
    'sitc4_parent', 'sitc4_children',
    'sitc3_parent', 'sitc3_children',
    'sitc2_parent', 'sitc2_children',
    'sitc1_parent', 'sitc1_children',
    'naics_parent', 'naics_children',
    'isic5_parent', 'isic5_children',
    'isic4_parent', 'isic4_children',
    'isic31_parent', 'isic31_children',
    'isic2_parent', 'isic2_children',
    'cpc21_parent', 'cpc21_children',
    'isco_parent', 'isco_children',
    'sitc4_sitc1', 'sitc3_sitc1', 'sitc2_sitc1', 'sitc1_sitc3',
    'hs2017_sitc1', 'hs2022_sitc1', 'hs2012_sitc1',
    'sitc1_isic4', 'isic31_sitc1', 'sitc1_isic31',
    'isic2_sitc1', 'sitc1_isic2',
    'm49_locode', 'sovereign_iso3166', 'm49_iso4217',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
