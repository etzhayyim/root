CREATE TABLE IF NOT EXISTS vertex_gameka_spec (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      spec_id VARCHAR, brief VARCHAR, title VARCHAR, slug VARCHAR,
      genre VARCHAR, mechanic_json VARCHAR, scene_json VARCHAR,
      budget_usd DOUBLE PRECISION, score DOUBLE PRECISION, rationale VARCHAR,
      iteration BIGINT, lineage_parent VARCHAR, model_id VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gameka_spec_slug
      ON vertex_gameka_spec (slug);

CREATE INDEX IF NOT EXISTS idx_gameka_spec_score_created
      ON vertex_gameka_spec (score DESC, created_at DESC);

CREATE TABLE IF NOT EXISTS vertex_gameka_artifact (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      artifact_id VARCHAR, spec_id VARCHAR,
      wasm_cid VARCHAR, wasm_size BIGINT, wasm_url VARCHAR,
      build_log_url VARCHAR, build_status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gameka_artifact_spec
      ON vertex_gameka_artifact (spec_id, created_at DESC);

CREATE TABLE IF NOT EXISTS vertex_gameka_qa (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      qa_id VARCHAR, artifact_id VARCHAR,
      fps_p50 DOUBLE PRECISION, crashes BIGINT, asset_404 BIGINT,
      scene_load_ms BIGINT, llm_score DOUBLE PRECISION,
      publish BOOLEAN, issues_json VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gameka_qa_artifact
      ON vertex_gameka_qa (artifact_id, created_at DESC);

CREATE TABLE IF NOT EXISTS vertex_gameka_title (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      title_id VARCHAR, slug VARCHAR, sub_did VARCHAR,
      parent_spec_id VARCHAR, parent_artifact_id VARCHAR,
      play_url VARCHAR, version VARCHAR,
      published_at VARCHAR, created_at VARCHAR,
      org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gameka_title_slug
      ON vertex_gameka_title (slug);

CREATE INDEX IF NOT EXISTS idx_gameka_title_sub_did
      ON vertex_gameka_title (sub_did);

CREATE TABLE IF NOT EXISTS edge_gameka_spec_revises (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      iteration BIGINT, score_delta DOUBLE PRECISION,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gameka_spec_revises_src
      ON edge_gameka_spec_revises (src_vid);

CREATE TABLE IF NOT EXISTS edge_gameka_title_published_by (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      published_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gameka_title_published_by_dst
      ON edge_gameka_title_published_by (dst_vid);
