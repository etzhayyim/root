import type { Kysely } from 'kysely';

/**
 * Compatibility placeholder.
 *
 * This migration name exists in production migration history,
 * but the original file is no longer present in this branch.
 * Keep as a no-op so Kysely migrator can validate executed history.
 */
export async function up(_db: Kysely<unknown>): Promise<void> {
  // no-op
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // no-op
}
