import { Kysely } from 'kysely';

/**
 * Compatibility stub.
 *
 * The live RisingWave cluster records a kysely_migration row named
 * `20260416240000_vertex_game_title_natural_person_coverage` (applied
 * 2026-04-16), but the sibling file was committed without the
 * `_coverage` suffix: `20260416240000_vertex_game_title_natural_person.ts`.
 * That mismatch makes Kysely's migrator reject the migration set as
 * "corrupted — previously executed migration ... is missing" and blocks
 * every subsequent `pnpm db:migrate` run.
 *
 * This file exists solely to satisfy Kysely's file-vs-ledger
 * reconciliation. `up()` and `down()` are no-ops; the actual DDL lives
 * in `20260416240000_vertex_game_title_natural_person.ts` (already
 * applied and recorded under the same timestamp but the non-suffixed
 * name — the two names collide on timestamp but Kysely keys off the
 * full filename, so one stub per ledger name is the unblock).
 *
 * Do not add DDL here. If the mismatch is ever resolved at the ledger
 * level (DELETE the `_coverage` row), this file can be removed.
 */
export async function up(_db: Kysely<unknown>): Promise<void> {
  // no-op — real DDL already applied under the sibling filename.
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // no-op
}
