import { Kysely, sql } from 'kysely';

/**
 * Migration 0005: vertex_gitrepo dedicated table for git-server worker.
 *
 * Replaces legacy GitRepo nodes that were stored in vertex_software via SQL.
 * git-server worker (50-infra/cloudflare/workers/git-server/worker.js) writes
 * here directly via Kysely + Hyperdrive (RisingWave).
 *
 * vertex_id convention: 'gitrepo:' + name
 */
export async function up(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_gitrepo" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "name" VARCHAR(256),
    "nanoid" VARCHAR(64),
    "template" VARCHAR(128),
    "head_sha" VARCHAR(64),
    "head_ref" VARCHAR(256),
    "org_id" VARCHAR(64),
    "user_id" VARCHAR(64),
    "actor_id" VARCHAR(64),
    "updated_at" VARCHAR(64)
  )`.compile(db));
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.schema.dropTable('vertex_gitrepo').ifExists().execute();
}
