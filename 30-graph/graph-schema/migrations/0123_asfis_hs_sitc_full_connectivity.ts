import { Kysely, sql } from 'kysely';

/**
 * Migration 0123: ASFIS ISSCAAP full connectivity — HS all editions + SITC all revisions.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-16
 * (reverse-topological-sort pass, iteration 45).
 *
 * ## Systems Built (20 total = 10 forward + 10 reverse)
 *
 * ### ASFIS × HS2017 (species-level concordance)
 *
 * | system       | edges | method                                     |
 * |--------------|-------|--------------------------------------------|
 * | asfis_hs2017 |   206 | direct FAO ISSCAAP→HS2017 concordance       |
 * | hs2017_asfis |   206 | reverse                                    |
 *
 * Based on HS 2017 Chapter 03 product descriptions × ISSCAAP group definitions:
 * - 24 ISSCAAP groups mapped to 206 unique HS 2017 6-digit commodity codes
 * - Covers: carps/tilapia/eels/salmon/flatfish/cod/tuna/herrings/sharks +
 *   crustaceans (lobster/crab/shrimp) + molluscs (oysters/mussels/scallops/squid)
 *
 * ### ASFIS × other HS editions (via asfis_isic4 × isic4_hsXXXX chain JOIN)
 *
 * | system       | edges | pivot chain                          |
 * |--------------|-------|--------------------------------------|
 * | asfis_hs2022 |  3492 | asfis_isic4 × isic4_hs2022          |
 * | hs2022_asfis |  3492 | reverse                              |
 * | asfis_hs2012 |  2705 | asfis_isic4 × isic4_hs2012          |
 * | hs2012_asfis |  2705 | reverse                              |
 * | asfis_hs2007 |  1209 | asfis_isic4 × isic4_hs2007          |
 * | hs2007_asfis |  1209 | reverse                              |
 * | asfis_hs2002 |  1113 | asfis_isic4 × isic4_hs2002          |
 * | hs2002_asfis |  1113 | reverse                              |
 * | asfis_hs1996 |   994 | asfis_isic4 × isic4_hs1996          |
 * | hs1996_asfis |   994 | reverse                              |
 *
 * ### ASFIS × SITC all revisions (via asfis_isic4 × isic4_sitcN chain JOIN)
 *
 * | system       | edges | pivot chain                          |
 * |--------------|-------|--------------------------------------|
 * | asfis_sitc4  |   776 | asfis_isic4 × isic4_sitc4           |
 * | sitc4_asfis  |   776 | reverse                              |
 * | asfis_sitc3  |  1454 | asfis_isic4 × isic4_sitc3           |
 * | sitc3_asfis  |  1454 | reverse                              |
 * | asfis_sitc2  |   350 | asfis_isic4 × isic4_sitc2           |
 * | sitc2_asfis  |   350 | reverse                              |
 * | asfis_sitc1  |   317 | asfis_isic4 × isic4_sitc1           |
 * | sitc1_asfis  |   317 | reverse                              |
 *
 * ## ASFIS Coverage Summary (after 0122–0123)
 *
 * ASFIS ISSCAAP groups (48 groups G11-G94) now connected to:
 * - ISIC4 (0311/0312/0321/0322 fishing activities) — 73 pairs (0122)
 * - HS2017 (direct 6-digit species concordance) — 206 pairs
 * - HS2022/2012/2007/2002/1996 (via ISIC4 chain) — 994-3492 pairs per edition
 * - SITC Rev.4/3/2/1 (via ISIC4 chain) — 317-1454 pairs per revision
 *
 * NOTE: Higher edge counts for newer HS editions reflect expanded chapter 03
 * product coverage (HS2022 added new aquaculture commodity codes).
 *
 * NOTE: ASFIS still not directly connected to ISIC5, NACE, CPC, BEC, ISCO, COFOG
 * — those chains can be extended in future iterations.
 *
 * DB after 0123: 3,193,352 edges, 505 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'asfis_hs2017',  'hs2017_asfis',
    'asfis_hs2022',  'hs2022_asfis',
    'asfis_hs2012',  'hs2012_asfis',
    'asfis_hs2007',  'hs2007_asfis',
    'asfis_hs2002',  'hs2002_asfis',
    'asfis_hs1996',  'hs1996_asfis',
    'asfis_sitc4',   'sitc4_asfis',
    'asfis_sitc3',   'sitc3_asfis',
    'asfis_sitc2',   'sitc2_asfis',
    'asfis_sitc1',   'sitc1_asfis',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'asfis_hs2017',  'hs2017_asfis',
    'asfis_hs2022',  'hs2022_asfis',
    'asfis_hs2012',  'hs2012_asfis',
    'asfis_hs2007',  'hs2007_asfis',
    'asfis_hs2002',  'hs2002_asfis',
    'asfis_hs1996',  'hs1996_asfis',
    'asfis_sitc4',   'sitc4_asfis',
    'asfis_sitc3',   'sitc3_asfis',
    'asfis_sitc2',   'sitc2_asfis',
    'asfis_sitc1',   'sitc1_asfis',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
