CREATE INDEX IF NOT EXISTS idx_repository_blob_owner_hash ON vertex_repository_blob (owner_did, hash);

CREATE INDEX IF NOT EXISTS idx_repository_blob_hash ON vertex_repository_blob (hash);

CREATE INDEX IF NOT EXISTS idx_repository_blob_created ON vertex_repository_blob (created_at);

CREATE INDEX IF NOT EXISTS idx_repository_tree_owner_hash ON vertex_repository_tree (owner_did, tree_hash);

CREATE INDEX IF NOT EXISTS idx_repository_tree_created ON vertex_repository_tree (created_at);

CREATE INDEX IF NOT EXISTS idx_repository_commit_owner_hash ON vertex_repository_commit (owner_did, commit_hash);

CREATE INDEX IF NOT EXISTS idx_repository_commit_tree_hash ON vertex_repository_commit (tree_hash);

CREATE INDEX IF NOT EXISTS idx_repository_commit_author ON vertex_repository_commit (author_did, author_timestamp);

CREATE INDEX IF NOT EXISTS idx_repository_commit_owner_time ON vertex_repository_commit (owner_did, committer_timestamp);

CREATE INDEX IF NOT EXISTS idx_repository_ref_owner_name ON vertex_repository_ref (owner_did, ref_name);

CREATE INDEX IF NOT EXISTS idx_repository_ref_owner_kind ON vertex_repository_ref (owner_did, kind);

CREATE INDEX IF NOT EXISTS idx_repository_ref_head ON vertex_repository_ref (head_commit_hash);

CREATE INDEX IF NOT EXISTS idx_edge_repository_parent_src ON edge_repository_parent (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_parent_dst ON edge_repository_parent (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_tree_src ON edge_repository_tree (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_tree_dst ON edge_repository_tree (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_entry_src_path ON edge_repository_entry (src_vid, path);

CREATE INDEX IF NOT EXISTS idx_edge_repository_entry_dst ON edge_repository_entry (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_authored_by_src ON edge_repository_authored_by (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_authored_by_dst ON edge_repository_authored_by (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_ref_points_src ON edge_repository_ref_points (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_ref_points_dst ON edge_repository_ref_points (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_ref_points_owner_time ON edge_repository_ref_points (owner_did, pushed_at);

CREATE INDEX IF NOT EXISTS idx_edge_repository_ref_owner_src ON edge_repository_ref_owner (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_repository_ref_owner_dst ON edge_repository_ref_owner (dst_vid);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_repository_activity_by_owner AS
    SELECT
      owner_did,
      count(*) AS commit_count,
      max(committer_timestamp) AS latest_commit_at
    FROM vertex_repository_commit
    GROUP BY owner_did;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_repository_ref_heads AS
    SELECT
      r.owner_did,
      r.ref_name,
      r.kind,
      r.head_commit_hash,
      r.updated_at,
      p.dst_vid AS head_commit_vid
    FROM vertex_repository_ref r
    LEFT JOIN edge_repository_ref_points p ON p.src_vid = r.vertex_id;
