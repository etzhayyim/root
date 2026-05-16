import { Kysely, sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * Bluesky post semantic search read model.
 *
 * RisingWave vector indexes require append-only inputs. Keep this table narrow:
 * immutable post identity + denormalized display fields + one native vector(384)
 * embedding. Re-embedding appends a new row with a different model_id instead
 * of mutating the existing row.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_bluesky_post_embedding (
      vertex_id     VARCHAR,
      source_uri    VARCHAR,
      source_cid    VARCHAR,
      repo          VARCHAR,
      rkey          VARCHAR,
      handle        VARCHAR,
      text          VARCHAR,
      created_at    VARCHAR,
      indexed_at    VARCHAR,
      emb           vector(384),
      model_id      VARCHAR,
      embedded_at   VARCHAR
    ) APPEND ONLY
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_bluesky_post_embedding_hnsw
    ON vertex_bluesky_post_embedding
    USING HNSW (emb)
    INCLUDE (source_uri, source_cid, repo, rkey, handle, text, created_at, indexed_at, model_id)
    WITH (distance_type = 'cosine', m = 16, ef_construction = 200)
  `.execute(db);
  await sql`FLUSH`.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_bluesky_post_embedding_repo
    ON vertex_bluesky_post_embedding(repo)
  `.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_bluesky_post_embedding_repo`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_bluesky_post_embedding_hnsw`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_bluesky_post_embedding`.execute(db);
  await sql`FLUSH`.execute(db);
}
