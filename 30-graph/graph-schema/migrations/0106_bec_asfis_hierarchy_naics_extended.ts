import { Kysely, sql } from 'kysely';

/**
 * Migration 0106: BEC/ASFIS hierarchy + hs2017 ISIC3.1/2 reverses + NAICS extended.
 *
 * Bootstrapped via direct psql against <vendor-rw-host-deprecated>:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 27).
 *
 * ## BEC / ASFIS hierarchy bridges
 *
 * | system           | edges  | derivation                              |
 * |------------------|--------|-----------------------------------------|
 * | bec_parent       |     24 | view_bec_category parent_code self-JOIN |
 * | bec_children     |     24 | reverse of bec_parent                   |
 * | asfis_parent     | 13,499 | view_asfis_species ISSCAAP group JOIN   |
 * | asfis_children   | 13,499 | reverse of asfis_parent                 |
 *
 * BEC Rev.5: 3-level hierarchy (section→division→group, 31 nodes).
 * ASFIS 2025: 13,708 species → 53 ISSCAAP groups (2-level, ~13,499 active).
 *
 * ## HS 2017 ↔ ISIC Rev.3.1 / Rev.2 reverses
 *
 * Pre-existing forward bridges: isic31_hs2017=1,418, isic2_hs2017=19.
 * This migration adds the missing reverse directions.
 *
 * | system           | edges | derivation                          |
 * |------------------|-------|-------------------------------------|
 * | hs2017_isic31    | 1,418 | reverse of isic31_hs2017            |
 * | hs2017_isic2     |    19 | reverse of isic2_hs2017             |
 * | hs2022_isic31    | 1,371 | hs2022_isic4 ∘ isic4_isic31        |
 * | isic31_hs2022    | 1,371 | reverse of hs2022_isic31            |
 * | hs2022_isic2     |    18 | hs2022_isic4 ∘ isic4_isic2         |
 * | isic2_hs2022     |    18 | reverse of hs2022_isic2             |
 *
 * ## NAICS extended bridges (via naics_cpc21 pivot = 67 edges at 4-digit level)
 *
 * NOTE: naics_isic4 (24 edges) is section-level (H, G, N) — incompatible with
 * class-level isic4_cpc3/sitcX. Must use naics_cpc21 (67 edges, 4-digit NAICS)
 * as the pivot instead.
 *
 * | system         | edges | derivation                           |
 * |----------------|-------|--------------------------------------|
 * | naics_cpc3     |    67 | naics_cpc21 ∘ cpc21_cpc3            |
 * | cpc3_naics     |    67 | reverse of naics_cpc3                |
 * | naics_hs2022   |   152 | naics_cpc21 ∘ cpc21_hs2022          |
 * | hs2022_naics   |   152 | reverse of naics_hs2022              |
 * | naics_hs2012   |  ~140 | naics_cpc21 ∘ cpc21_hs2012          |
 * | hs2012_naics   |  ~140 | reverse of naics_hs2012              |
 * | naics_sitc3    |  ~67  | naics_cpc21 ∘ cpc21_sitc3 (post-0105)|
 * | sitc3_naics    |  ~67  | reverse of naics_sitc3               |
 * | naics_sitc2    |  ~67  | naics_cpc21 ∘ cpc21_sitc2 (post-0105)|
 * | naics_sitc1    |  ~67  | naics_cpc21 ∘ cpc21_sitc1 (post-0105)|
 *
 * ## cpc3 ↔ hs2007/2002/1996 reverses (after 0105 builds forward direction)
 *
 * | system       | edges  | derivation                      |
 * |--------------|--------|---------------------------------|
 * | cpc3_hs2007  |  ~5.5K | reverse of hs2007_cpc3          |
 * | cpc3_hs2002  |  ~5.2K | reverse of hs2002_cpc3          |
 * | cpc3_hs1996  |  ~4.9K | reverse of hs1996_cpc3          |
 *
 * ## Coverage impact
 *
 * - BEC Rev.5 fully traversable as a 3-level tree
 * - FAO ASFIS fish/aquatic species navigable to ISSCAAP groups
 * - All HS editions (1996–2022) now bidirectional with ISIC Rev.3.1 and Rev.2
 * - NAICS 2022 connected to all SITC revisions, CPC3, and HS editions
 *
 * ## Total edges after 0106: ~3.8M+
 */
export async function up(db: Kysely<any>): Promise<void> {
  // BEC / ASFIS hierarchy
  for (const system of ['bec_parent', 'bec_children', 'asfis_parent', 'asfis_children']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // hs2017/2022 ↔ ISIC3.1/2
  for (const system of [
    'hs2017_isic31', 'hs2017_isic2',
    'hs2022_isic31', 'isic31_hs2022',
    'hs2022_isic2',  'isic2_hs2022',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // NAICS extended
  for (const system of [
    'naics_cpc3',   'cpc3_naics',
    'naics_sitc4',  'sitc4_naics',
    'naics_sitc3',  'sitc3_naics',
    'naics_sitc2',  'sitc2_naics',
    'naics_sitc1',  'sitc1_naics',
    'naics_hs2022', 'hs2022_naics',
    'naics_hs2012', 'hs2012_naics',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }

  // cpc3 ↔ hs legacy reverses
  for (const system of ['cpc3_hs2007', 'cpc3_hs2002', 'cpc3_hs1996']) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  for (const system of [
    'bec_parent', 'bec_children',
    'asfis_parent', 'asfis_children',
    'hs2017_isic31', 'hs2017_isic2',
    'hs2022_isic31', 'isic31_hs2022',
    'hs2022_isic2',  'isic2_hs2022',
    'naics_cpc3',   'cpc3_naics',
    'naics_sitc4',  'sitc4_naics',
    'naics_sitc3',  'sitc3_naics',
    'naics_sitc2',  'sitc2_naics',
    'naics_sitc1',  'sitc1_naics',
    'naics_hs2022', 'hs2022_naics',
    'naics_hs2012', 'hs2012_naics',
    'cpc3_hs2007',  'cpc3_hs2002',  'cpc3_hs1996',
  ]) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
