CREATE INDEX IF NOT EXISTS idx_vertex_repo_commit_repo_seq ON vertex_repo_commit(repo, seq);

DROP INDEX IF EXISTS idx_vertex_repo_root_rev;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_repo_root;

DROP TABLE IF EXISTS vertex_repo_root;
