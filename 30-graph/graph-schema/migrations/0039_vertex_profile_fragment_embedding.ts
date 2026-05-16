import type { Kysely } from 'kysely';
import { sql } from 'kysely';

export async function up(db: Kysely<unknown>): Promise<void> {
  await db.executeQuery(sql`
    ALTER TABLE "vertex_profile_fragment"
    ADD COLUMN IF NOT EXISTS "embedding" REAL[]
  `.compile(db));
  await db.executeQuery(sql`
    ALTER TABLE "vertex_profile_fragment"
    ADD COLUMN IF NOT EXISTS "embedding_norm" DOUBLE PRECISION
  `.compile(db));
  await db.executeQuery(sql`
    ALTER TABLE "vertex_profile_fragment"
    ADD COLUMN IF NOT EXISTS "ivf_cluster_id" BIGINT
  `.compile(db));
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await db.executeQuery(sql`
    ALTER TABLE "vertex_profile_fragment"
    DROP COLUMN IF EXISTS "ivf_cluster_id"
  `.compile(db));
  await db.executeQuery(sql`
    ALTER TABLE "vertex_profile_fragment"
    DROP COLUMN IF EXISTS "embedding_norm"
  `.compile(db));
  await db.executeQuery(sql`
    ALTER TABLE "vertex_profile_fragment"
    DROP COLUMN IF EXISTS "embedding"
  `.compile(db));
}
