CREATE TABLE IF NOT EXISTS vertex_shinshi_aesthetic_review (
  vertex_id VARCHAR PRIMARY KEY,
  owner_did VARCHAR,
  post_uri VARCHAR NOT NULL,
  image_url TEXT,
  review_mode VARCHAR NOT NULL,
  review_model VARCHAR NOT NULL,
  score DOUBLE PRECISION,
  reasons_json TEXT,
  latency_ms BIGINT,
  status VARCHAR,
  error TEXT,
  created_at VARCHAR,
  updated_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR,
  sensitivity_ord BIGINT
);

CREATE INDEX IF NOT EXISTS idx_shinshi_aesthetic_review_lookup
  ON vertex_shinshi_aesthetic_review (post_uri, review_mode, review_model);
