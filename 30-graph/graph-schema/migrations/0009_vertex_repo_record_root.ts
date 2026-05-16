import { Kysely } from 'kysely';

/**
 * Historical migration-name compatibility shim.
 *
 * Production RisingWave already recorded this migration under the old name
 * `0009_vertex_repo_record_root`. The canonical file in-repo is now
 * `0011_vertex_repo_record_root.ts`, but Kysely treats missing historical
 * filenames as corruption and aborts before later migrations can run.
 *
 * This shim exists only to satisfy migration history integrity. It is never
 * expected to execute on production because the name is already present in
 * `kysely_migration`.
 */
export async function up(_db: Kysely<any>): Promise<void> {}

export async function down(_db: Kysely<any>): Promise<void> {}
