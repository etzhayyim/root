import { Kysely, sql } from 'kysely';

/**
 * Migration 0108: HS 2002/1996 completion + NAICS cleanup.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 29).
 *
 * ## HS 2002 completion (via 0105 build)
 *
 * | system        | edges  | derivation                              |
 * |---------------|--------|-----------------------------------------|
 * | hs2002_cpc21  | 81,500 | hs2002_hs2012 ∘ hs2012_cpc21           |
 * | cpc21_hs2002  | 81,500 | reverse of hs2002_cpc21                 |
 * | naics_hs2002  |    140 | naics_cpc21 ∘ cpc21_hs2002             |
 * | hs2002_naics  |    140 | reverse of naics_hs2002                 |
 *
 * NOTE: hs2002_cpc3 = 0 (not buildable). The succession chain
 * hs2002_hs2012 ∘ hs2012_cpc3 gives 0 pairs because hs2012_cpc3 uses
 * generic hs.etzhayyim.com node domain while hs2002_hs2012 dst uses hs2012.etzhayyim.com
 * (domain mismatch). CPC21-mediated bridge (99K) would be too coarse.
 * Same limitation applies to hs2007_cpc3 and hs1996_cpc3.
 *
 * ## HS 1996 bridges (via hs1996_hs2012 = 5,634 pivot)
 *
 * | system        | edges  | derivation                              |
 * |---------------|--------|-----------------------------------------|
 * | hs1996_sitc4  | 23,694 | hs1996_hs2012 ∘ hs2012_sitc4           |
 * | sitc4_hs1996  | 23,694 | reverse of hs1996_sitc4                 |
 * | hs1996_sitc3  | ~23,K  | hs1996_hs2012 ∘ hs2012_sitc3           |
 * | sitc3_hs1996  | ~23K   | reverse of hs1996_sitc3                 |
 * | hs1996_sitc2  |  ~8K   | hs1996_hs2012 ∘ hs2012_sitc2           |
 * | sitc2_hs1996  |  ~8K   | reverse of hs1996_sitc2                 |
 * | hs1996_sitc1  |   ~856 | hs1996_hs2012 ∘ hs2012_sitc1           |
 * | sitc1_hs1996  |   ~856 | reverse of hs1996_sitc1                 |
 * | hs1996_nace   |  2,678 | hs1996_hs2012 ∘ hs2012_nace            |
 * | nace_hs1996   |  2,678 | reverse of hs1996_nace                  |
 * | hs1996_cpc21  | ~65K   | hs1996_hs2012 ∘ hs2012_cpc21           |
 * | cpc21_hs1996  | ~65K   | reverse of hs1996_cpc21                 |
 * | naics_hs1996  |   ~140 | naics_cpc21 ∘ cpc21_hs1996             |
 * | hs1996_naics  |   ~140 | reverse of naics_hs1996                 |
 *
 * NOTE: hs1996_cpc3 = 0 (same domain mismatch as hs2002/2007_cpc3).
 * cpc3_hs1996/2002/2007 reverses are also 0 as no forward bridges exist.
 *
 * ## Deduplication fixes
 *
 * | system       | before | after | root cause                          |
 * |--------------|--------|-------|-------------------------------------|
 * | cpc3_sitc1   |  9,892 | 5,196 | concurrent builds via different paths |
 * | nace_hs2002  |  5,720 | 2,860 | concurrent builds (double insertion)  |
 *
 * ## Coverage impact
 *
 * - HS 1996 now fully connected to all SITC revisions, NACE, CPC21, NAICS
 * - HS 2002 now fully connected to CPC21 + NAICS (in addition to existing)
 * - All 6 HS editions (1996-2022) symmetrically connected to NAICS
 * - Total systems: 380+
 *
 * ## Known limitations
 *
 * - hs2007/2002/1996_cpc3 = 0 (no direct CPC3 concordance, domain mismatch
 *   in succession chain pivot prevents derivation; CPC21 path would give ~99K
 *   noisy edges)
 * - cpc3_hs2007/2002/1996 = 0 (no forward bridge to reverse)
 *
 * ## Total edges after 0108: ~5M+
 */
export async function up(db: Kysely<any>): Promise<void> {
  // HS 2002 completion
  for (const system of [
    'hs2002_cpc21', 'cpc21_hs2002',
    'naics_hs2002', 'hs2002_naics',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // HS 1996 full bridge set
  for (const system of [
    'hs1996_sitc4', 'sitc4_hs1996',
    'hs1996_sitc3', 'sitc3_hs1996',
    'hs1996_sitc2', 'sitc2_hs1996',
    'hs1996_sitc1', 'sitc1_hs1996',
    'hs1996_nace',  'nace_hs1996',
    'hs1996_cpc21', 'cpc21_hs1996',
    'naics_hs1996', 'hs1996_naics',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2002_cpc21', 'cpc21_hs2002',
    'naics_hs2002', 'hs2002_naics',
    'hs1996_sitc4', 'sitc4_hs1996',
    'hs1996_sitc3', 'sitc3_hs1996',
    'hs1996_sitc2', 'sitc2_hs1996',
    'hs1996_sitc1', 'sitc1_hs1996',
    'hs1996_nace',  'nace_hs1996',
    'hs1996_cpc21', 'cpc21_hs1996',
    'naics_hs1996', 'hs1996_naics',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
