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
    ) APPEND ONLY;

FLUSH;

CREATE INDEX IF NOT EXISTS idx_bluesky_post_embedding_hnsw
    ON vertex_bluesky_post_embedding
    USING HNSW (emb)
    INCLUDE (source_uri, source_cid, repo, rkey, handle, text, created_at, indexed_at, model_id)
    WITH (distance_type = 'cosine', m = 16, ef_construction = 200);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_bluesky_post_embedding_repo
    ON vertex_bluesky_post_embedding(repo);

FLUSH;
