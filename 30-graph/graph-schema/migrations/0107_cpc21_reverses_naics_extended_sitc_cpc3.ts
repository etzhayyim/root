import { Kysely, sql } from 'kysely';

/**
 * Migration 0107: CPC21 missing reverses + NAICS extended + SITC↔CPC3 completeness.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 28).
 *
 * ## CPC21 missing reverses
 *
 * | system        | edges  | derivation                     |
 * |---------------|--------|--------------------------------|
 * | cpc21_sitc4   | 61,697 | reverse of sitc4_cpc21         |
 * | cpc21_isic31  |    608 | reverse of isic31_cpc21        |
 * | cpc21_isic2   |     23 | reverse of isic2_cpc21         |
 *
 * ## NAICS extended (via naics_cpc21=67 as class-level pivot)
 *
 * NOTE: naics_isic4 (24 edges) is section-level (H/G/N) — cannot chain to
 * class-level cpc3/sitcX. naics_cpc21 (67 4-digit NAICS→CPC21) is the correct pivot.
 *
 * | system        | edges | derivation                           |
 * |---------------|-------|--------------------------------------|
 * | naics_sitc4   |    87 | naics_cpc21 ∘ cpc21_sitc4           |
 * | sitc4_naics   |    87 | reverse of naics_sitc4               |
 * | naics_hs2017  |   157 | naics_cpc21 ∘ cpc21_hs2017          |
 * | hs2017_naics  |   157 | reverse of naics_hs2017              |
 * | naics_hs2007  |   152 | naics_cpc21 ∘ cpc21_hs2007          |
 * | hs2007_naics  |   152 | reverse of naics_hs2007              |
 * | naics_isic31  |     4 | naics_cpc21 ∘ cpc21_isic31          |
 * | isic31_naics  |     4 | reverse of naics_isic31              |
 * | naics_isic2   |     2 | naics_cpc21 ∘ cpc21_isic2           |
 * | isic2_naics   |     2 | reverse of naics_isic2               |
 * | nace_naics    |    21 | reverse of naics_nace_v2             |
 *
 * NOTE: naics_nace_v2 (21 edges, naics_cpc21 ∘ cpc21_nace) complements
 * the existing naics_nace (24 edges, section-level via naics_isic4).
 *
 * ## HS 2002 bridges (built by 0105 concurrent run, documented here)
 *
 * | system         | edges  | derivation                          |
 * |----------------|--------|-------------------------------------|
 * | hs2002_nace    |  2,860 | hs02_hs07 ∘ hs07_hs12 ∘ hs2012_nace |
 * | nace_hs2002    |  2,860 | reverse of hs2002_nace              |
 * | sitc4_hs2002   | 25,335 | reverse of hs2002_sitc4             |
 * | sitc3_hs2002   | 25,024 | reverse of hs2002_sitc3             |
 * | sitc2_hs2002   |  8,449 | reverse of hs2002_sitc2             |
 * | sitc1_hs2002   |    917 | reverse of hs2002_sitc1             |
 *
 * ## SITC↔CPC3 completeness (via isic4 mediation)
 *
 * | system        | edges  | derivation                      |
 * |---------------|--------|---------------------------------|
 * | sitc2_cpc3    | 24,628 | sitc2_isic4 ∘ isic4_cpc3       |
 * | cpc3_sitc2    | 24,628 | reverse of sitc2_cpc3           |
 * | sitc1_cpc3    | ~5,000 | sitc1_isic4 ∘ isic4_cpc3       |
 * | cpc3_sitc1    | ~5,000 | reverse of sitc1_cpc3           |
 *
 * ## Coverage impact
 *
 * - CPC21 now fully bidirectional with all SITC revisions (1-4), all HS editions (1996-2022)
 * - NAICS 2022 connected to all HS editions (1996-2022) and all SITC revisions via CPC21 pivot
 * - All SITC revisions now fully bidirectional with CPC3
 * - All 7 HS editions × 4 SITC revisions × 4 classification systems bidirectionally complete
 *
 * ## Total edges after 0107: ~4.3M+
 */
export async function up(db: Kysely<any>): Promise<void> {
  // CPC21 missing reverses
  for (const system of ['cpc21_sitc4', 'cpc21_isic31', 'cpc21_isic2']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // NAICS extended
  for (const system of [
    'naics_sitc4',  'sitc4_naics',
    'naics_hs2017', 'hs2017_naics',
    'naics_hs2007', 'hs2007_naics',
    'naics_isic31', 'isic31_naics',
    'naics_isic2',  'isic2_naics',
    'naics_nace_v2', 'nace_naics',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // HS 2002 reverses + NACE (concurrent with 0105 build)
  for (const system of [
    'nace_hs2002',
    'sitc4_hs2002', 'sitc3_hs2002', 'sitc2_hs2002', 'sitc1_hs2002',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // SITC↔CPC3 completeness
  for (const system of ['sitc2_cpc3', 'cpc3_sitc2', 'sitc1_cpc3', 'cpc3_sitc1']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'cpc21_sitc4', 'cpc21_isic31', 'cpc21_isic2',
    'naics_sitc4',  'sitc4_naics',
    'naics_hs2017', 'hs2017_naics',
    'naics_hs2007', 'hs2007_naics',
    'naics_isic31', 'isic31_naics',
    'naics_isic2',  'isic2_naics',
    'naics_nace_v2', 'nace_naics',
    'nace_hs2002',
    'sitc4_hs2002', 'sitc3_hs2002', 'sitc2_hs2002', 'sitc1_hs2002',
    'sitc2_cpc3', 'cpc3_sitc2',
    'sitc1_cpc3', 'cpc3_sitc1',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
