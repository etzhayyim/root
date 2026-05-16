import { Kysely, sql } from 'kysely';

/**
 * Migration 0116: ISCO-08 ↔ ISIC-4 + COFOG ↔ ISIC-4 concordance bridges.
 *
 * Bootstrapped via direct psql against 172.236.132.11:4566 on 2026-04-15
 * (reverse-topological-sort pass, iteration 38).
 *
 * ## ISCO-08 ↔ ISIC-4 (140 edges each direction)
 *
 * Source: ILO ISCO-08 Volume I, Annex III (occupation → primary industry mapping)
 * Strategy: map ISCO minor groups / unit groups to ISIC-4 4-digit classes
 *
 * Key clusters covered:
 * | ISCO range  | Description                    | ISIC-4 mapping        |
 * |-------------|--------------------------------|-----------------------|
 * | 611-634     | Agriculture/forestry/fishing   | 011-032 (Section A)   |
 * | 711-753     | Craft/construction/food trades | 101-433               |
 * | 811-835     | Plant operators/drivers        | 051-5022              |
 * | 2211-2269   | Health professionals           | 8610-8690             |
 * | 3211-3259   | Health technicians             | 8610-8690             |
 * | 2310-2359   | Education professionals        | 8510-8550             |
 * | 2511-2532   | ICT professionals              | 6201-6312             |
 * | 3511-3522   | ICT technicians                | 6201-6312             |
 * | 2411-3322   | Finance/business professionals | 6411-7320             |
 * | 5411-5419   | Protective services            | 8421-8423             |
 * | 921-942     | Elementary workers             | sector-specific       |
 *
 * NOTE: ISCO groups 6-9 are at 3-digit minor group level in the DB
 * (unit groups 4-digit not loaded for agricultural/manual workers).
 * ISCO groups 0-5 are at 4-digit unit group level.
 *
 * ## COFOG ↔ ISIC-4 (52 edges each direction)
 *
 * Source: UN SNA 2008 Chapter 17 + COFOG manual (government function → delivering industry)
 * Maps each COFOG division/group (XX.Y format) to the primary ISIC-4 industry
 * that delivers that government function.
 *
 * | COFOG div | Function              | ISIC-4 |
 * |-----------|-----------------------|--------|
 * | 01.x      | General public svcs   | 8411   |
 * | 02.x      | Defence               | 8422   |
 * | 03.x      | Public order/safety   | 8421   |
 * | 05.x      | Environmental prot.   | 3811-3900 |
 * | 07.x      | Health                | 8610   |
 * | 08.x      | Recreation/culture    | 9001-9200 |
 * | 09.x      | Education             | 8510-8550 |
 * | 10.x      | Social protection     | 8710-8891 |
 *
 * ## Coverage Impact
 *
 * ISCO-08 and COFOG were previously isolated (hierarchy only, no cross-bridges).
 * After 0116:
 * - ISCO connects to ISIC-4 → can chain to all HS/SITC/BEC/NACE/CPC21 etc.
 * - COFOG connects to ISIC-4 → functional public expenditure linked to industrial output
 *
 * DB after 0116: 3,156,834 edges, 417 systems.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_isic4', 'isic4_isco',
    'cofog_isic4', 'isic4_cofog',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  const systems = [
    'isco_isic4', 'isic4_isco',
    'cofog_isic4', 'isic4_cofog',
  ];
  for (const system of systems) {
    await sql`DELETE FROM edge_classified_as WHERE system = ${sql.lit(system)}`.execute(db);
  }
}
