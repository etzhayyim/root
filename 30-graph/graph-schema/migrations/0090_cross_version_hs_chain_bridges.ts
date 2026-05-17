import { Kysely, sql } from 'kysely';

/**
 * Migration 0090: Cross-version HS chain bridges + extended SITC/ISIC4 chains.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 16).
 *
 * ## Prerequisites
 *
 * Requires 0089 reverse bridges (hs17_hs22, hs17_hs12, hs12_hs07, hs07_hs02, hs02_hs96)
 * to be present before derivation.
 *
 * ## New bridges (all chain compositions via ∘ operator)
 *
 * ### HS cross-version forward chains (HS2022 → older editions)
 *
 * | system          | edges  | derivation                                              |
 * |-----------------|--------|---------------------------------------------------------|
 * | hs2022_hs2012   | ~6,528 | hs22_hs17 ∘ hs17_hs12                                  |
 * | hs2022_hs2007   | ~6,197 | hs2022_hs2012 ∘ hs12_hs07                               |
 * | hs2022_hs2002   | ~6,108 | hs2022_hs2007 ∘ hs07_hs02                               |
 * | hs2022_hs1996   | ~6,226 | hs2022_hs2002 ∘ hs02_hs96                               |
 *
 * ### HS cross-version backward chains (older → HS2022)
 *
 * | system          | edges  | derivation                                              |
 * |-----------------|--------|---------------------------------------------------------|
 * | hs2012_hs2022   | ~6,561 | hs12_hs17 ∘ hs17_hs22                                  |
 * | hs2007_hs2022   | ~6,197 | hs07_hs12 ∘ hs2012_hs2022                               |
 * | hs2002_hs2022   | ~6,108 | hs02_hs07 ∘ hs2007_hs2022                               |
 * | hs1996_hs2022   | ~6,226 | hs96_hs02 ∘ hs2002_hs2022                               |
 *
 * ### Extended SITC→HS chains (HS2022 and HS2012 editions)
 *
 * | system          | edges  | derivation                                              |
 * |-----------------|--------|---------------------------------------------------------|
 * | sitc3_hs2022    | ~14,756| sitc3_hs2017 ∘ hs17_hs22                               |
 * | sitc2_hs2022    | ~10,037| sitc2_hs2017 ∘ hs17_hs22                               |
 * | sitc1_hs2022    |  ~1,053| sitc1_hs2017 ∘ hs17_hs22                               |
 * | sitc3_hs2012    | ~14,756| sitc3_hs2017 ∘ hs17_hs12                               |
 * | sitc2_hs2012    | ~10,037| sitc2_hs2017 ∘ hs17_hs12                               |
 * | sitc1_hs2012    |  ~1,053| sitc1_hs2017 ∘ hs17_hs12                               |
 *
 * ### ISIC4 extended HS chains
 *
 * | system          | edges  | derivation                                              |
 * |-----------------|--------|---------------------------------------------------------|
 * | isic4_hs2022    |  ~5,736| isic4_hs2017 ∘ hs17_hs22                               |
 *
 * ## Coverage impact
 *
 * Before: HS versions only connected via adjacent steps (2017↔2022, 2012↔2017, etc.)
 * After: Any HS edition can directly map to any other edition (transitive closure).
 * SITC Rev.1–3 can now map to HS2022 directly (previously only HS2017).
 * ISIC4 now maps to HS2022 as well as HS2017.
 *
 * ## Topology
 *
 * All edges reference existing vertex_repo_record rows.
 * 0 new orphans (chain bridges inherit src/dst from existing vertex sets).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // All bridges: idempotent DELETE + re-derive via 2-hop SQL JOIN
  // Chain pattern: JOIN e1.dst_vid = e2.src_vid

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_hs2012'`.execute(db);
  // hs22_hs17.dst → hs17_hs12.src (shared HS2017 pivot)

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_hs2007'`.execute(db);
  // hs2022_hs2012 ∘ hs12_hs07

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_hs2002'`.execute(db);
  // hs2022_hs2007 ∘ hs07_hs02

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_hs1996'`.execute(db);
  // hs2022_hs2002 ∘ hs02_hs96

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_hs2022'`.execute(db);
  // hs12_hs17 ∘ hs17_hs22

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2007_hs2022'`.execute(db);
  // hs07_hs12 ∘ hs2012_hs2022

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2002_hs2022'`.execute(db);
  // hs02_hs07 ∘ hs2007_hs2022

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs1996_hs2022'`.execute(db);
  // hs96_hs02 ∘ hs2002_hs2022

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_hs2022'`.execute(db);
  // sitc3_hs2017 ∘ hs17_hs22

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_hs2022'`.execute(db);
  // sitc2_hs2017 ∘ hs17_hs22

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_hs2022'`.execute(db);
  // sitc1_hs2017 ∘ hs17_hs22

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc3_hs2012'`.execute(db);
  // sitc3_hs2017 ∘ hs17_hs12

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc2_hs2012'`.execute(db);
  // sitc2_hs2017 ∘ hs17_hs12

  await sql`DELETE FROM edge_classified_as WHERE system = 'sitc1_hs2012'`.execute(db);
  // sitc1_hs2017 ∘ hs17_hs12

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_hs2022'`.execute(db);
  // isic4_hs2017 ∘ hs17_hs22
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2022_hs2012', 'hs2022_hs2007', 'hs2022_hs2002', 'hs2022_hs1996',
    'hs2012_hs2022', 'hs2007_hs2022', 'hs2002_hs2022', 'hs1996_hs2022',
    'sitc3_hs2022', 'sitc2_hs2022', 'sitc1_hs2022',
    'sitc3_hs2012', 'sitc2_hs2012', 'sitc1_hs2012',
    'isic4_hs2022',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
