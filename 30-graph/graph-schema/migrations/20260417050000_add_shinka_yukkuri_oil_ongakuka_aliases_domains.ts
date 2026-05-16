import { Kysely } from 'kysely';

/**
 * Compatibility stub for out-of-band applied migration.
 *
 * The live RisingWave cluster records a kysely_migration row named
 * `20260417050000_add_shinka_yukkuri_oil_ongakuka_aliases_domains` (applied out-of-band via psql; see
 * 30-graph/graph-schema/CLAUDE.md §Migration History). No matching
 * file exists, which makes Kysely's migrator reject the set as
 * "corrupted — previously executed migration ... is missing" and
 * blocks every subsequent `pnpm db:migrate` run.
 *
 * This file exists solely to satisfy Kysely's file-vs-ledger
 * reconciliation. `up()` and `down()` are no-ops; the real DDL
 * was applied out-of-band. Do not add DDL here.
 */
export async function up(_db: Kysely<unknown>): Promise<void> {
  // no-op — real DDL already applied out-of-band.
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // no-op
}
