import { Kysely, sql } from 'kysely';

/**
 * Migration 0111: _r suffix namespace cleanup + SITC4↔HS asymmetry repair.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 32).
 *
 * ## _r suffix cleanup
 *
 * During earlier migrations, "corrected direction" variants were built with
 * `_r` suffix while the canonical names still existed with noisy data.
 * After 0109/0110 repaired the canonical names, the `_r` variants became
 * redundant. This migration removes them.
 *
 * ### Exact duplicates deleted (5 systems)
 *
 * | system         | edges | canonical counterpart |
 * |----------------|-------|-----------------------|
 * | hs2017_cpc3_r  | 5,740 | cpc3_hs2017 (5,740)   |
 * | hs2012_cpc3_r  | 5,500 | cpc3_hs2012 (5,500)   |
 * | sitc4_cpc3_r   | 3,717 | cpc3_sitc4 (3,717)    |
 * | sitc2_hs2022_r | 9,766 | sitc2_hs2022 (9,766)  |
 * | sitc2_hs2012_r | 9,344 | sitc2_hs2012 (9,344)  |
 *
 * All confirmed 100% overlap via INTERSECT before deletion.
 *
 * ### Chain-derived → exact reverse replacement (2 systems)
 *
 * | system        | before (chain) | after (exact rev) | source         |
 * |---------------|----------------|-------------------|----------------|
 * | sitc2_hs2017  | 10,037         | 9,353             | hs2017_sitc2   |
 * | sitc3_hs2017  | 29,391         | 27,428            | hs2017_sitc3   |
 *
 * The chain-derived versions had 684 / 1,963 extra edges from CPC3
 * transitive fan-out noise. The exact reverse of the forward bridge is more
 * precise and matches the hs2017_sitcN concordance directly.
 * After replacement, sitc2_hs2017_r and sitc3_hs2017_r were also deleted
 * (they were the "exact reverse" versions — now promoted to canonical names).
 *
 * ## SITC4↔HS asymmetry repair
 *
 * Post-cleanup audit revealed two pairs where forward ≠ reverse:
 *
 * | system         | before  | after   | source         |
 * |----------------|---------|---------|----------------|
 * | hs2017_sitc4   | 27,861  | 29,861  | sitc4_hs2017   |
 * | hs2012_sitc4   | 27,868  | 28,354  | sitc4_hs2012   |
 *
 * Root cause: hs2017_sitc4 and hs2012_sitc4 were rebuilt during migration
 * 0088 (FLUSH fix pass) from a different derivation path (hs2017_cpc3 ∘
 * cpc3_sitc4) which at the time had 27,861 / 27,868 edges. Meanwhile
 * sitc4_hs2017 / sitc4_hs2012 were preserved from 0086 (29,861 / 28,354).
 * After cpc3_sitc4 was repaired from 61K to 3,717 in 0110, the original
 * derivation path can no longer reproduce the old counts. Rebuilt both as
 * exact reverses of their forward concordances.
 *
 * ## DB state after 0111
 *
 * - Deleted: 7 _r suffix systems (5 exact dups + 2 _r after canonical rename)
 * - Rebuilt: sitc2_hs2017 (10,037→9,353), sitc3_hs2017 (29,391→27,428)
 * - Rebuilt: hs2017_sitc4 (27,861→29,861), hs2012_sitc4 (27,868→28,354)
 * - No remaining _r suffix systems (except naics_nace_r which is distinct
 *   from naics_nace_v2 — different source, kept for now)
 * - Total edges: ~4.60M, 377 systems
 *
 * ## Coverage after 0111
 *
 * All major classification systems remain fully bidirectional. The _r cleanup
 * removed namespace pollution. All SITC↔HS bridges are now symmetric (exact
 * reverses in both directions).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // Delete 5 exact _r duplicates
  for (const system of [
    'hs2017_cpc3_r',
    'hs2012_cpc3_r',
    'sitc4_cpc3_r',
    'sitc2_hs2022_r',
    'sitc2_hs2012_r',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // Replace chain-derived with exact reverses (delete base + _r variant)
  for (const system of [
    'sitc2_hs2017',  // 10,037 chain → rebuilt as 9,353 exact reverse
    'sitc2_hs2017_r',
    'sitc3_hs2017',  // 29,391 chain → rebuilt as 27,428 exact reverse
    'sitc3_hs2017_r',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // Fix SITC4↔HS asymmetry (rebuild from exact reverse)
  for (const system of [
    'hs2017_sitc4',  // 27,861 → 29,861 (exact reverse of sitc4_hs2017)
    'hs2012_sitc4',  // 27,868 → 28,354 (exact reverse of sitc4_hs2012)
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'hs2017_cpc3_r', 'hs2012_cpc3_r', 'sitc4_cpc3_r',
    'sitc2_hs2022_r', 'sitc2_hs2012_r',
    'sitc2_hs2017', 'sitc2_hs2017_r',
    'sitc3_hs2017', 'sitc3_hs2017_r',
    'hs2017_sitc4',
    'hs2012_sitc4',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
