// tier: C
// L2 Actor embedding — narrow per-actor row storing a 384-d vector
// (multilingual-e5-small) of `display_name || description || kind`.
//
// Storage model:
//   - vertex_id is the natural PK (matches source vertex row)
//   - did + kind duplicated from view_actor_universal for index-only scans
//   - embedding VARCHAR holding comma-joined float32 text (portable across
//     RW versions that haven't shipped native pgvector TYPE yet). L3 IVF
//     migration swaps VARCHAR → vector(384) when the extension lands.
//   - embedded_at for incremental re-embed triggered by source update
//
// Feed pipeline (NOT in this migration):
//   1. Murakumo MLX batch job reads from view_actor_universal WHERE vertex_id
//      NOT IN (SELECT vertex_id FROM vertex_actor_embedding)
//   2. POST text → multilingual-e5-small → 384 float32
//   3. INSERT INTO vertex_actor_embedding VALUES (...)
//
// Shannon cost per actor: 1 embedding UDF call (amortized ~2ms in batch).
//
// References:
//   - ADR-0044 Python External UDF with io_threads=100
//   - 90-docs/260417-codex-etzhayyim-mv-live-reads-deployment-runbook.md
//   - migrations/0039_vertex_profile_fragment_embedding.ts (pattern)
import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`CREATE TABLE IF NOT EXISTS vertex_actor_embedding (
    vertex_id      VARCHAR PRIMARY KEY,
    _seq           BIGINT,
    created_date   DATE,
    sensitivity_ord BIGINT,
    owner_did      VARCHAR,

    did            VARCHAR,        -- path-DID from derive_did()
    kind           VARCHAR,        -- vertex_<kind> suffix
    embedding      VARCHAR,        -- 384 float32, comma-joined. VARCHAR until pgvector lands.
    embedding_norm REAL,           -- L2 norm (for cosine eval without recompute)
    model_id       VARCHAR,        -- 'multilingual-e5-small-v1' (tracks re-embed drift)
    embedded_at    VARCHAR,
    org_id         VARCHAR DEFAULT 'anon',
    user_id        VARCHAR DEFAULT 'anon',
    actor_id       VARCHAR DEFAULT '',
    created_at     VARCHAR
  )`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_actor_embedding_kind
    ON vertex_actor_embedding(kind)`.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_actor_embedding_did
    ON vertex_actor_embedding(did)`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_actor_embedding_did`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_actor_embedding_kind`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_actor_embedding`.execute(db);
  await sql`FLUSH`.execute(db);
}
