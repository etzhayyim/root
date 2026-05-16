import { Kysely, sql } from 'kysely';

/**
 * Migration 0086: HS↔SITC4 bidirectional derived bridges.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 12).
 *
 * ## New concordance bridges (all derived — no new taxonomy masters)
 *
 * | system          | edges  | derivation                                              |
 * |-----------------|--------|---------------------------------------------------------|
 * | hs2017_sitc4    | 29,861 | HS2017 → SITC4 (reverse of sitc4_hs2017)               |
 * | hs2022_sitc4    | 29,052 | HS2022 ↔ SITC4 via shared HS2017 node                  |
 * | hs2012_sitc4    | 27,868 | HS2012 ↔ SITC4 via hs12_hs17 ∘ sitc4_hs2017 reverse   |
 *
 * ### Derivation methodology
 * **Reverse bridge**: swap src_vid ↔ dst_vid of sitc4_hs2017.
 * **Shared node**: JOIN hs22_hs17.dst_vid = sitc4_hs2017.dst_vid (HS2017 is shared).
 * **Chain + reverse**: JOIN hs12_hs17.dst_vid = sitc4_hs2017.dst_vid (HS2017 as pivot).
 *
 * ## Coverage impact
 *
 * Before: lookup direction was SITC→HS only (sitc4_hs2017, sitc4_hs2012).
 * After: HS→SITC lookups enabled for HS 2012, 2017, 2022 editions.
 * Full SITC↔HS cross-classification now bidirectional.
 *
 * ## Full concordance inventory (44 systems, 632,471 total edges):
 *   locode_iso3166 (115,687), atc_ndc (69,740),
 *   hs2017_sitc4 (29,861), hs2022_sitc4 (29,052), sitc4_hs2017 (29,861),
 *   sitc4_hs2012 (28,354), hs2012_sitc4 (27,868), sitc3_hs2017 (14,756),
 *   sitc2_hs2017 (10,053), hs22_hs17 (6,561), hs12_hs17 (6,528),
 *   hs96_hs02 (6,226), hs07_hs12 (6,197), hs02_hs07 (6,108),
 *   hs2017 (5,843), hs2017_cpc3 (5,740), hs2012 (5,584), hs2012_cpc3 (5,500),
 *   sitc3_sitc4 (5,408), cpc3 (4,391), sitc4 (3,776), sitc4_cpc3 (3,717),
 *   sitc2_sitc3 (2,805), sitc2_sitc4 (2,693), cpc (2,663), cpc_isic5 (2,504),
 *   sitc1_sitc2 (1,334), sitc1_sitc4 (1,115), sitc1_hs2017 (1,053),
 *   isic5 (700), nace_r2 (679), isic5_nace (625), isic31_isic5 (231),
 *   isic31_isic4 (229), sovereign_m49 (219), iso3166_sovereign (215),
 *   iso3166_m49 (215), iso4217_iso3166 (164), isic2_isic31 (76),
 *   naics_isic5 (24), naics_isic4 (24), ipc (1)
 *   (excl. openalex_concept 159,739)
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2017_sitc4'`.execute(db);
  // SELECT DISTINCT e1.dst_vid, e1.src_vid FROM edge_classified_as e1 WHERE system='sitc4_hs2017'

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2022_sitc4'`.execute(db);
  // SELECT DISTINCT e1.src_vid, e2.src_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.dst_vid = e2.dst_vid
  // WHERE e1.system='hs22_hs17' AND e2.system='sitc4_hs2017'

  await sql`DELETE FROM edge_classified_as WHERE system = 'hs2012_sitc4'`.execute(db);
  // SELECT DISTINCT e1.src_vid, e2.src_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.dst_vid = e2.dst_vid
  // WHERE e1.system='hs12_hs17' AND e2.system='sitc4_hs2017'
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of ['hs2017_sitc4', 'hs2022_sitc4', 'hs2012_sitc4']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
