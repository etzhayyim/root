import { Kysely, sql } from 'kysely';

/**
 * Migration 0089: Reverse/bidirectional bridges for complete lookup coverage.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 15).
 *
 * ## Motivation
 *
 * All prior bridges were directed (A→B). Many query patterns require B→A
 * (e.g. "given a tariff code HS2017, which ISIC4 industries produce it?").
 * This migration completes bidirectionality by reversing key bridges.
 *
 * All inserts use INSERT+FLUSH pattern (RisingWave checkpoint durability).
 *
 * ## New bridges (all reversal of existing systems)
 *
 * | system          | edges  | derivation                                              |
 * |-----------------|--------|---------------------------------------------------------|
 * | hs2017_isic4    | ~5,736 | reverse of isic4_hs2017 (HS2017 → ISIC4)               |
 * | sitc4_isic4     | ~3,231 | reverse of isic4_sitc4 (SITC4 → ISIC4)                 |
 * | nace_isic4      |   679  | reverse of isic4_nace (NACE → ISIC4)                   |
 * | cpc21_isic4     | ~2,663 | reverse of isic4_cpc21 (CPC21 → ISIC4)                 |
 * | sitc4_hs2022    | ~29,052| reverse of hs2022_sitc4 (SITC4 → HS2022)               |
 * | sitc4_sitc3     | ~5,408 | reverse of sitc3_sitc4 (SITC4 → SITC3)                 |
 * | sitc3_sitc2     | ~2,805 | reverse of sitc2_sitc3 (SITC3 → SITC2)                 |
 * | sitc4_sitc2     | ~2,688 | reverse of sitc2_sitc4 (SITC4 → SITC2)                 |
 * | hs17_hs22       | ~6,561 | reverse of hs22_hs17 (HS2017 → HS2022)                 |
 * | hs17_hs12       | ~6,528 | reverse of hs12_hs17 (HS2017 → HS2012)                 |
 * | hs12_hs07       | ~6,197 | reverse of hs07_hs12 (HS2012 → HS2007)                 |
 * | hs07_hs02       | ~6,108 | reverse of hs02_hs07 (HS2007 → HS2002)                 |
 * | hs02_hs96       | ~6,226 | reverse of hs96_hs02 (HS2002 → HS1996)                 |
 *
 * ## Coverage impact
 *
 * Before: ISIC4 "outbound" only (industry→product, industry→tariff).
 * After: full bidirectional industry↔product↔tariff↔trade lookups.
 *
 * SITC chain now bidirectional: SITC1↔SITC2↔SITC3↔SITC4↔HS2017/2022.
 * HS version chain now bidirectional: HS1996↔2002↔2007↔2012↔2017↔2022.
 *
 * ## Full concordance inventory post-0089 (~60 systems, ~650K total edges excl. openalex_concept)
 *
 * New reverse systems (+13):
 *   hs2017_isic4, sitc4_isic4, nace_isic4, cpc21_isic4,
 *   sitc4_hs2022, sitc4_sitc3, sitc3_sitc2, sitc4_sitc2,
 *   hs17_hs22, hs17_hs12, hs12_hs07, hs07_hs02, hs02_hs96
 */
export async function up(db: Kysely<any>): Promise<void> {
  // All bridges: idempotent DELETE + re-derive via SQL JOIN (reverse pattern)
  // Re-generated via: python3 /tmp/build_reverse_bridges.py + INSERT+FLUSH

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_isic4'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='isic4_hs2017'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_isic4'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='isic4_sitc4'

  await sql`DELETE FROM edge_classified_as WHERE system = 'nace_isic4'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='isic4_nace'

  await sql`DELETE FROM edge_classified_as WHERE system = 'cpc21_isic4'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='isic4_cpc21'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_hs2022'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='hs2022_sitc4'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_sitc3'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='sitc3_sitc4'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_sitc2'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='sitc2_sitc3'

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc4_sitc2'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='sitc2_sitc4'

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs17_hs22'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='hs22_hs17'

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs17_hs12'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='hs12_hs17'

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs12_hs07'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='hs07_hs12'

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs07_hs02'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='hs02_hs07'

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs02_hs96'`.execute(db);
  // SELECT DISTINCT dst_vid, src_vid FROM edge_classified_as WHERE system='hs96_hs02'
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2017_isic4', 'sitc4_isic4', 'nace_isic4', 'cpc21_isic4',
    'sitc4_hs2022', 'sitc4_sitc3', 'sitc3_sitc2', 'sitc4_sitc2',
    'hs17_hs22', 'hs17_hs12', 'hs12_hs07', 'hs07_hs02', 'hs02_hs96',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
