import { Kysely, sql } from 'kysely';

/**
 * Drop legacy `val TEXT` columns from `vertex_actor` and `vertex_actor_manifest`.
 *
 * Background: P10v2 GraphAr-native design uses promoted typed columns only
 * (no JSON aggregate column). The `val TEXT` column is a P9 holdover from
 * the original `0001_initial_schema.ts`. Static grep across the monorepo
 * shows zero reads/writes of `vertex_actor.val` or
 * `vertex_actor_manifest.val` from app code (TypeScript), so drop is safe.
 *
 * See `90-docs/260407-kagami-p10v2-graphar-native-design.md`.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE "vertex_actor" DROP COLUMN IF EXISTS "val"`.execute(db);
  await sql`ALTER TABLE "vertex_actor_manifest" DROP COLUMN IF EXISTS "val"`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`ALTER TABLE "vertex_actor" ADD COLUMN IF NOT EXISTS "val" TEXT`.execute(db);
  await sql`ALTER TABLE "vertex_actor_manifest" ADD COLUMN IF NOT EXISTS "val" TEXT`.execute(db);
}
