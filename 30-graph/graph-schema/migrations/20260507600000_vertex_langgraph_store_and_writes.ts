import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2605080600: LangGraph Server + Granian L3 Runtime
// tier: C

/**
 * vertex_langgraph_checkpoint_write
 *   pending writes per (thread_id, checkpoint_ns, checkpoint_id, task_id).
 *   Required by RisingWaveCheckpointSaver.aput_writes().
 *
 * vertex_langgraph_store
 *   cross-thread long-term memory (BaseStore).
 *   namespace = "/".join(actor_did, collection, ...) convention.
 *   Required by RisingWaveStore.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_langgraph_checkpoint_write (
      vertex_id    VARCHAR PRIMARY KEY,
      _seq         BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      thread_id    VARCHAR NOT NULL,
      checkpoint_id VARCHAR NOT NULL,
      checkpoint_ns VARCHAR NOT NULL DEFAULT '',
      task_id      VARCHAR NOT NULL,
      task_path    VARCHAR NOT NULL DEFAULT '',
      idx          INTEGER NOT NULL,
      channel      VARCHAR NOT NULL,
      type         VARCHAR NOT NULL DEFAULT 'json',
      blob         VARCHAR,
      created_at   VARCHAR,
      actor_did    VARCHAR,
      org_did      VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_langgraph_write_lookup
      ON vertex_langgraph_checkpoint_write (thread_id, checkpoint_ns, checkpoint_id, idx ASC)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_langgraph_store (
      vertex_id    VARCHAR PRIMARY KEY,
      _seq         BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      namespace    VARCHAR NOT NULL,
      key          VARCHAR NOT NULL,
      value        VARCHAR,
      created_at   VARCHAR,
      updated_at   VARCHAR,
      actor_did    VARCHAR,
      org_did      VARCHAR DEFAULT 'anon'
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_langgraph_store_ns
      ON vertex_langgraph_store (namespace, updated_at DESC)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_langgraph_store_ns`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_langgraph_store`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_langgraph_write_lookup`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_langgraph_checkpoint_write`.execute(db);
}
