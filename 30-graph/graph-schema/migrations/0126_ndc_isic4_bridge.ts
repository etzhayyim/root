import { Kysely, sql } from 'kysely';

/**
 * Migration 0126: NDC (National Drug Code) → ISIC4 pharmaceutical bridge.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 48).
 *
 * ## Systems Built (2 total)
 *
 * | system    | edges   | method                                                |
 * |-----------|---------|-------------------------------------------------------|
 * | ndc_isic4 | 125,340 | ndc→atc-L5 → L5[0]=L1 → atc_isic4 chain             |
 * | isic4_ndc | 125,340 | reverse                                               |
 *
 * ## Approach
 *
 * The `ndc_atc` bridge (69,740 edges) links FDA NDC product codes to ATC L5
 * specific substance codes (e.g., B03AA03). The `atc_isic4` bridge maps ATC L1
 * group codes (single letter A-V) to ISIC4 pharma manufacturing (21/210/2100).
 *
 * Since the L1 ancestor of any ATC Lx code is its first character, we extract
 * the L1 prefix (ndc_atc.dst_vid.last_segment[0]) and join to atc_isic4.
 * This avoids the full 5-hop hierarchy climb.
 *
 * Result: 41,780 unique FDA NDC drug products × 3 ISIC4 codes = 125,340 pairs.
 * All 14 ATC L1 groups (A-V) mapped to ISIC4 21/210/2100 (pharma manufacturing).
 *
 * ## Design Note: NDC Extended Chains Intentionally Not Built
 *
 * The natural chain ndc_isic4 × isic4_hs2017 would produce ~4.26M pairs
 * (41,780 NDC drugs × ~102 pharma HS codes). This Cartesian product is
 * technically correct but semantically un-useful (all drugs share the same
 * pharma HS headings) and would dominate the edge_classified_as table.
 *
 * For direct NDC→HS concordance, an FDA NDC→HS mapping table is needed.
 * Currently no such mapping is available in the DB.
 *
 * ## NDC Coverage Summary (after 0126)
 *
 * 69,740 FDA NDC products now connected to ISIC4 pharma manufacturing sector.
 * Path: NDC → ATC substance → ISIC4 21 (pharma) → any trade classification.
 *
 * DB after 0126: 3,465,602 edges, 569 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'ndc_isic4', 'isic4_ndc',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'ndc_isic4', 'isic4_ndc',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
