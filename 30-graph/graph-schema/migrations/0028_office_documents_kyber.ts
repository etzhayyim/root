import type { Kysely } from 'kysely';

/**
 * Compatibility stub for a production-applied migration that is still present
 * in `kysely_migration` but whose original source is no longer in-tree.
 *
 * This keeps the Kysely migrator able to enumerate the historical chain
 * without mutating current schema state.
 */
export async function up(_db: Kysely<unknown>): Promise<void> {}

export async function down(_db: Kysely<unknown>): Promise<void> {}
