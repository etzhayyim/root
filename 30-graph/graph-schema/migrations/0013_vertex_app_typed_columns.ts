import { Kysely, sql } from 'kysely';

/**
 * Migration 0013 — typed columns on vertex_app for App metadata previously
 * stuffed into a props JSON blob.
 *
 * Fields surfaced from the resolveActorVisibility / buildProfileView /
 * appMetaRow code paths in the atproto worker:
 *
 *   sensitivity      — "public" | "internal" | "confidential" | "restricted"
 *   performer_type   — "service" | "human" | "collective"
 *   content_mode     — "timeline" | "appview" | "embed"
 *   ui_type          — "appview" | "timeline" | "embed"
 *   embed_url        — HTTPS URL for App embed hosting
 *   classification   — governance classification label
 *   app_did          — canonical vanity DID for multi-DID apps
 */
export async function up(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "sensitivity" VARCHAR(32)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "performer_type" VARCHAR(32)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "content_mode" VARCHAR(32)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "ui_type" VARCHAR(32)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "embed_url" VARCHAR(512)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "classification" VARCHAR(64)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "app_did" VARCHAR(512)`.compile(db));
}

export async function down(_db: Kysely<any>): Promise<void> {
  // Forward-only.
}
