import { Kysely, sql } from 'kysely';

/**
 * Migration 0004: Rename repo log tables to vertex/edge naming convention.
 *
 * Before:
 *   repo_commit           — AT Protocol commit log (append-only queue)
 *   repo_block            — IPLD block store (content-addressed)
 *   graph_consumer_cursor — Graph Worker consumer offset
 *
 * After:
 *   vertex_repo_commit    — same schema, vertex_* naming
 *   vertex_repo_block     — same schema, vertex_* naming
 *   vertex_consumer_cursor — same schema, vertex_* naming
 *
 * Note: RisingWave does not support ALTER TABLE RENAME, so we CREATE new tables.
 * The old tables are dropped in down(). Production migration requires data copy.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // vertex_repo_commit — AT Protocol commit log (append-only queue)
  // vertex_id = repo + ':seq:' + seq (unique per commit event)
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_repo_commit" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "seq" BIGINT,
    "repo" VARCHAR(512),
    "collection" VARCHAR(512),
    "rkey" VARCHAR(64),
    "action" VARCHAR(16),
    "rev" VARCHAR(64),
    "cid" VARCHAR(512),
    "prev" VARCHAR(512),
    "sig" TEXT,
    "value_json" TEXT,
    "ts_ms" BIGINT,
    "record_cid" VARCHAR(512),
    "created_at" VARCHAR(64)
  )`.compile(db));

  // vertex_repo_block — IPLD block store (content-addressed)
  // vertex_id = repo + '/' + cid
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_repo_block" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "cid" VARCHAR(512),
    "repo" VARCHAR(512),
    "content" TEXT,
    "size_bytes" BIGINT,
    "created_at" VARCHAR(64)
  )`.compile(db));

  // vertex_consumer_cursor — Graph Worker consumer offset
  // vertex_id = consumer_id (unique per consumer)
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_consumer_cursor" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "consumer_id" VARCHAR(256),
    "last_seq" BIGINT,
    "updated_at" VARCHAR(64)
  )`.compile(db));
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.schema.dropTable('vertex_repo_commit').ifExists().execute();
  await db.schema.dropTable('vertex_repo_block').ifExists().execute();
  await db.schema.dropTable('vertex_consumer_cursor').ifExists().execute();
}
