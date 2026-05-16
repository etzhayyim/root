CREATE TABLE IF NOT EXISTS vertex_repo_root (
    did VARCHAR PRIMARY KEY,
    cid VARCHAR NOT NULL,
    rev VARCHAR NOT NULL,
    indexed_at VARCHAR NOT NULL,
    created_at VARCHAR NOT NULL
  );

CREATE INDEX IF NOT EXISTS idx_vertex_repo_root_rev ON vertex_repo_root(rev);

DROP INDEX IF EXISTS idx_vertex_repo_commit_repo_seq;
