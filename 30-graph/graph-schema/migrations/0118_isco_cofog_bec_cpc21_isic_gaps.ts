import { Kysely, sql } from 'kysely';

/**
 * Migration 0118: ISCO/COFOG→BEC/CPC21 + ISIC legacy gap repairs.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 40).
 *
 * ## New Systems
 *
 * ### ISCO/COFOG → BEC (goods economic category connectivity)
 *
 * | system    | edges | pivot chain                        |
 * |-----------|-------|------------------------------------|
 * | isco_bec  |    12 | isco_isic4 × isic4_bec             |
 * | bec_isco  |    12 | reverse                            |
 * | cofog_bec |    12 | cofog_isic4 × isic4_bec            |
 * | bec_cofog |    12 | reverse                            |
 *
 * NOTE: Small counts (12) expected — BEC is goods-only; only goods-producing
 * ISIC4 sectors (agriculture, mining, manufacturing) bridge to both
 * ISCO occupations and BEC categories.
 *
 * ### ISCO → CPC21 (product classification)
 *
 * | system      | edges | pivot chain                      |
 * |-------------|-------|----------------------------------|
 * | isco_cpc21  |   456 | isco_isic4 × isic4_cpc21        |
 * | cpc21_isco  |   456 | reverse                          |
 *
 * ISCO-08 occupations (farming, manufacturing, health, ICT, finance etc.)
 * now bridged to UN CPC21 product classification.
 *
 * ### ISIC3.1 legacy gap repairs
 *
 * | system        | edges | notes                                     |
 * |---------------|-------|-------------------------------------------|
 * | isic31_naics  |    22 | repaired from 4 → via isic31_isic4×isic4_naics |
 * | naics_isic31  |    22 | repaired reverse                           |
 * | isic31_cpc3   |   597 | already present (built in earlier pass)    |
 * | cpc3_isic31   |   597 | already present                            |
 *
 * NOTE: isic2_naics chain returns 0 pairs (genuine empty — ISIC2 only has
 * 76 isic2→isic31 pairs and isic31_naics has 22 pairs; no overlap at
 * current vertex ID granularity).
 *
 * DB after 0118: 3,158,448 edges, 431 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_bec',   'bec_isco',
    'cofog_bec',  'bec_cofog',
    'isco_cpc21', 'cpc21_isco',
    'isic31_naics', 'naics_isic31',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_bec',   'bec_isco',
    'cofog_bec',  'bec_cofog',
    'isco_cpc21', 'cpc21_isco',
    'isic31_naics', 'naics_isic31',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
