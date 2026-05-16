import { Kysely, sql } from 'kysely';

/**
 * Migration 0017 — promote the last props-overflow fields on
 * vertex_project_props and vertex_convo so handler code can stop
 * parsing the JSON blob entirely.
 *
 *   vertex_project_props: kind / depth / email / description / priority
 *   vertex_convo: kind / members_json (fixed-shape array, not catch-all)
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_project_props extension columns ──
  await db.executeQuery(sql`ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "kind" VARCHAR(64)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "depth" BIGINT`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "email" VARCHAR(512)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "description" TEXT`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "priority" VARCHAR(32)`.compile(db));

  // ── vertex_convo extension columns ──
  await db.executeQuery(sql`ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "kind" VARCHAR(64)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "members_json" TEXT`.compile(db));
}

export async function down(_db: Kysely<any>): Promise<void> {
  // Forward-only.
}
