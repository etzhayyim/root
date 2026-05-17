import { Kysely, sql } from 'kysely';

/**
 * Migration 0087: ISIC Rev.4 cross-classification bridges (CPC21, HS2017, SITC4, NACE).
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 12).
 *
 * ## New concordance bridges (all derived — no new taxonomy masters)
 *
 * | system        | edges | derivation                                                   |
 * |---------------|-------|--------------------------------------------------------------|
 * | isic4_cpc21   | 2,504 | ISIC4 ↔ CPC21 via shared ISIC5 (isic5 JOIN cpc_isic5)       |
 * | isic4_hs2017  | 5,764 | ISIC4 → HS2017 via CPC21 (isic4_cpc21 ∘ hs2017)             |
 * | isic4_sitc4   | 3,213 | ISIC4 → SITC4 via CPC21 (isic4_cpc21 ∘ sitc4)               |
 * | isic4_nace    |   679 | ISIC4 → NACE Rev.2 (reverse of nace_r2)                     |
 *
 * ### Derivation methodology
 *
 * **isic4_cpc21** (shared ISIC5 pattern):
 *   - isic5: ISIC4(src) → ISIC5(dst)
 *   - cpc_isic5: CPC21(src) → ISIC5(dst)
 *   - JOIN on dst_vid: (ISIC4, CPC21) pairs sharing a common ISIC5 code
 *
 * **isic4_hs2017** (chain via CPC21):
 *   - isic4_cpc21: ISIC4(src) → CPC21(dst)
 *   - hs2017: CPC21(src) → HS2017(dst)
 *   - Chain JOIN on dst=src: ISIC4 → HS2017
 *
 * **isic4_sitc4** (chain via CPC21):
 *   - isic4_cpc21: ISIC4(src) → CPC21(dst)
 *   - sitc4: CPC21(src) → SITC4(dst)
 *   - Chain JOIN: ISIC4 → SITC4
 *
 * **isic4_nace** (reverse of nace_r2):
 *   - nace_r2: NACE(src) → ISIC4(dst)
 *   - Reverse: ISIC4(src) → NACE(dst)
 *
 * ## Coverage impact
 *
 * ISIC Rev.4 (industry activities) was previously only linked to ISIC5 and NACE.
 * After: ISIC4 → CPC21 (products) → HS2017 (tariff codes) → SITC4 (trade categories).
 * Enables: "which industries produce goods classified under HS chapter X?" queries.
 * Enables: "given a SITC trade category, which ISIC industries produce it?" (via reverse).
 *
 * ## Full concordance inventory (48 systems, ~686,757 total edges excl. openalex_concept):
 *   locode_iso3166 (115,687), atc_ndc (69,740),
 *   hs2017_sitc4 (29,861), sitc4_hs2017 (29,861), hs2022_sitc4 (29,052),
 *   sitc4_hs2012 (28,354), hs2012_sitc4 (27,868), sitc3_hs2017 (14,756),
 *   sitc2_hs2017 (10,053), hs22_hs17 (6,561), hs12_hs17 (6,528),
 *   hs96_hs02 (6,226), hs07_hs12 (6,197), hs02_hs07 (6,108),
 *   hs2017 (5,843), hs2017_cpc3 (5,740), isic4_hs2017 (5,764), hs2012 (5,584),
 *   hs2012_cpc3 (5,500), sitc3_sitc4 (5,408), cpc3 (4,391),
 *   sitc4 (3,776), sitc4_cpc3 (3,717), isic4_sitc4 (3,213), sitc2_sitc3 (2,805),
 *   sitc2_sitc4 (2,693), cpc (2,663), cpc_isic5 (2,504), isic4_cpc21 (2,504),
 *   sitc1_sitc2 (1,334), sitc1_sitc4 (1,115), sitc1_hs2017 (1,053),
 *   isic5 (700), nace_r2 (679), isic4_nace (679), isic5_nace (625),
 *   isic31_isic5 (231), isic31_isic4 (229), sovereign_m49 (219),
 *   iso3166_sovereign (215), iso3166_m49 (215), iso4217_iso3166 (164),
 *   isic2_isic31 (76), naics_isic5 (24), naics_isic4 (24), ipc (1)
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_cpc21'`.execute(db);
  // JOIN: isic5.dst_vid = cpc_isic5.dst_vid (shared ISIC5)
  // SELECT DISTINCT e1.src_vid, e2.src_vid FROM edge_classified_as e1
  // JOIN edge_classified_as e2 ON e1.dst_vid = e2.dst_vid
  // WHERE e1.system='isic5' AND e2.system='cpc_isic5'

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_hs2017'`.execute(db);
  // Chain: isic4_cpc21.dst_vid = hs2017.src_vid

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_sitc4'`.execute(db);
  // Chain: isic4_cpc21.dst_vid = sitc4.src_vid

  await sql`DELETE FROM edge_classified_as WHERE system = 'isic4_nace'`.execute(db);
  // Reverse of nace_r2: SELECT dst_vid as src, src_vid as dst FROM edge_classified_as WHERE system='nace_r2'
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of ['isic4_cpc21', 'isic4_hs2017', 'isic4_sitc4', 'isic4_nace']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
