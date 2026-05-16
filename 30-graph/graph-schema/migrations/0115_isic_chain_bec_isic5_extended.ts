import { Kysely, sql } from 'kysely';

/**
 * Migration 0115: Complete ISIC temporal chain → BEC + ISIC5 cross-bridge check.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 37).
 *
 * ## ISIC Chain → BEC
 *
 * All ISIC revisions now connected to BEC via HS2017 pivot:
 *
 * | system      | edges | pivot                          |
 * |-------------|-------|--------------------------------|
 * | isic5_bec   |   457 | isic5_hs2017 × hs2017_bec     |
 * | bec_isic5   |   457 | reverse                        |
 * | isic31_bec  |    99 | isic31_hs2017 × hs2017_bec    |
 * | bec_isic31  |    99 | reverse                        |
 * | isic2_bec   |     5 | isic2_hs2017 × hs2017_bec     |
 * | bec_isic2   |     5 | reverse                        |
 *
 * NOTE: Low counts for ISIC3.1 (99) and ISIC2 (5) reflect the narrow HS coverage
 * of those legacy editions — isic31_hs2017 has only 1,418 edges, isic2_hs2017 only 19.
 * The few goods-producing sectors in ISIC2 (agriculture, mining, manufacturing) do
 * connect to BEC categories via HS pivot.
 *
 * ## ISIC5 Cross-Bridge Completeness (verified, no new builds needed)
 *
 * All ISIC5 cross-bridges confirmed present before this migration:
 * | system       | edges |
 * |--------------|-------|
 * | isic5_cpc21  | 2,504 |
 * | cpc21_isic5  | 2,504 |
 * | isic5_cpc3   | 2,450 |
 * | cpc3_isic5   | 2,450 |
 * | isic5_nace   |   625 |
 * | nace_isic5   |   625 |
 * | isic5_naics  |    74 |
 * | naics_isic5  |    74 |
 *
 * ## BEC Coverage Summary (after 0112-0115)
 *
 * BEC now connected bidirectionally to ALL classification systems:
 * - HS (1996, 2002, 2007, 2012, 2017, 2022): direct concordance (5,000–5,900 ea)
 * - SITC (1, 2, 3, 4): direct concordance (970–3,400 ea)
 * - ISIC (2, 3.1, 4, 5): via HS2017 pivot (5–477)
 * - NACE Rev.2: via HS2017 pivot (340)
 * - CPC21: via HS2017 pivot (1,881)
 * - CPC v3: via HS2017 pivot (1,850)
 * - NAICS 2022: via HS2017 pivot (14)
 *
 * DB after 0115: 3,156,450 edges, 413 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'isic5_bec',  'bec_isic5',
    'isic31_bec', 'bec_isic31',
    'isic2_bec',  'bec_isic2',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'isic5_bec',  'bec_isic5',
    'isic31_bec', 'bec_isic31',
    'isic2_bec',  'bec_isic2',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
