CREATE TABLE IF NOT EXISTS vertex_repository_blob (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      hash VARCHAR,
      size_bytes BIGINT,
      tier VARCHAR,
      inline_text VARCHAR,
      bytes_ref VARCHAR,
      mime_type VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_repository_tree (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      tree_hash VARCHAR,
      entry_count BIGINT,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_repository_commit (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      commit_hash VARCHAR,
      tree_hash VARCHAR,
      author_did VARCHAR,
      committer_did VARCHAR,
      message VARCHAR,
      author_timestamp VARCHAR,
      committer_timestamp VARCHAR,
      signature_es256 VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_repository_ref (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      ref_name VARCHAR,
      kind VARCHAR,
      head_commit_hash VARCHAR,
      description VARCHAR,
      created_at VARCHAR, updated_at VARCHAR,
      org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_repository_parent (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      parent_ordinal BIGINT,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_repository_tree (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_repository_entry (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      path VARCHAR,
      mode VARCHAR,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_repository_authored_by (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      role VARCHAR,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_repository_ref_points (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      update_kind VARCHAR,
      reason VARCHAR,
      pushed_at VARCHAR,
      committer_did VARCHAR,
      created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_repository_ref_owner (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      created_at VARCHAR
    );
