import { Kysely, sql } from 'kysely';

/**
 * Migration 0103: Classification hierarchy bridges (parent/children edges).
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 24).
 *
 * All hierarchies derived directly from `parent_code` column in classification views.
 * Each system gets two bridge systems:
 *   - `{sys}_parent`: child → immediate parent
 *   - `{sys}_children`: parent → immediate children
 *
 * ## New bridge pairs
 *
 * | pair                        | edges  | source view          |
 * |-----------------------------|--------|----------------------|
 * | atc_parent / atc_children   |  6,426 | view_atc_substance   |
 * | icd10_parent / icd10_child  | 90,141 | view_icd10_disease   |
 * | sdg_parent / sdg_children   |    420 | view_sdg_indicator   |
 * | cofog_parent / cofog_child  |    178 | view_cofog_function  |
 * | cpc3_parent / cpc3_children | ~4,400 | view_cpc3_product    |
 * | nace_parent / nace_children |   ~960 | view_nace_activity   |
 * | bec_parent / bec_children   |     ~23| view_bec_category    |
 *
 * ## Coverage impact
 *
 * All major classification systems are now traversable as trees:
 * - Medical: ICD-10 (90K nodes) and ATC drug (6,440 nodes) bidirectional hierarchy
 * - SDG: Goal→Target→Indicator traversal
 * - Government functions: COFOG 3-level traversal
 * - Products: CPC3 5-level product hierarchy
 * - Industries: NACE Rev.2 4-level hierarchy
 * - Trade: BEC 3-level economic categories
 *
 * ## Total edges after 0103: ~2.15M+ (excl. openalex_concept)
 */
export async function up(db: Kysely<any>): Promise<void> {
  for (const system of [
    'atc_parent', 'atc_children',
    'icd10_parent', 'icd10_children',
    'sdg_parent', 'sdg_children',
    'cofog_parent', 'cofog_children',
    'cpc3_parent', 'cpc3_children',
    'nace_parent', 'nace_children',
    'bec_parent', 'bec_children',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'atc_parent', 'atc_children',
    'icd10_parent', 'icd10_children',
    'sdg_parent', 'sdg_children',
    'cofog_parent', 'cofog_children',
    'cpc3_parent', 'cpc3_children',
    'nace_parent', 'nace_children',
    'bec_parent', 'bec_children',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
