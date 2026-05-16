import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * vertex_langgraph_checkpoint — LangGraph durable state for pymagatama
 * shared UDF pool (ADR-0049 §Saver).
 *
 * Why not the stock LangGraph `PostgresSaver`:
 * RisingWave is a streaming DB, not OLTP. It does not implement
 * `SELECT FOR UPDATE` (no row-level locks) and transactions are
 * restricted. PostgresSaver assumes both.
 *
 * Design:
 * - Primary key = `{thread_id}:{checkpoint_id}` composite-in-string. This
 *   gives a natural upsert target without needing RW to materialize a
 *   composite unique constraint.
 * - `checkpoint_id` is a ULID-style time-sortable string generated client-
 *   side (`pymagatama.saver._new_checkpoint_id`). Monotonic per thread,
 *   so conflict resolution is last-write-wins by creation order —
 *   acceptable for LangGraph's append-only checkpoint semantics.
 * - No row lock. Writes use `INSERT ... ON CONFLICT (vertex_id) DO UPDATE
 *   SET blob = EXCLUDED.blob`. Concurrent writers to the same
 *   `(thread_id, checkpoint_id)` pair produce identical rows (ULID
 *   collision is negligible) so idempotent overwrite is safe.
 * - Reads: `SELECT blob ... WHERE thread_id = $1 ORDER BY checkpoint_id
 *   DESC LIMIT 1` — the primary index supports this in O(log n).
 *
 * Fork / ToT (Tree-of-Thoughts) is anticipated but not required in Mode A
 * (reactive agents typically do not fork). `parent_checkpoint_id` is
 * included for future use; consumer code ignores it today.
 *
 * Consumer:
 *   20-actors/magatama/py/src/pymagatama/saver.py::KyselyMirrorSaver
 *
 * Related:
 *   ADR-0049 §Saver
 *   ADR-0036 Worker-direct Hyperdrive (write path for VKE-internal clients)
 *   ADR-0048 Vultr VKE + B2 primary (target cluster)
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_langgraph_checkpoint (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      thread_id VARCHAR, checkpoint_id VARCHAR, checkpoint_ns VARCHAR,
      parent_checkpoint_id VARCHAR, checkpoint_type VARCHAR,
      blob VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    )
  `.execute(db);

  // Latest-per-thread read path — KyselyMirrorSaver.aget() primary query.
  // (thread_id, checkpoint_id DESC) gives O(log n) latest lookup.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_langgraph_checkpoint_thread_cid
      ON vertex_langgraph_checkpoint (thread_id, checkpoint_id DESC)
  `.execute(db);

  // Fork-tree traversal (ToT workflows). Unused by Mode A today; retained
  // so future agents can follow parent chains without a table migration.
  await sql`
    CREATE INDEX IF NOT EXISTS idx_langgraph_checkpoint_parent
      ON vertex_langgraph_checkpoint (parent_checkpoint_id)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_langgraph_checkpoint_parent`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_langgraph_checkpoint_thread_cid`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_langgraph_checkpoint`.execute(db);
}
