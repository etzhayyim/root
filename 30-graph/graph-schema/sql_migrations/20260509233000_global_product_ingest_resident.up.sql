CREATE TABLE IF NOT EXISTS vertex_product_ingest_frontier (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  frontier_id VARCHAR NOT NULL,
  frontier_kind VARCHAR NOT NULL,
  query VARCHAR,
  official_url VARCHAR,
  merchant_url VARCHAR,
  brand VARCHAR,
  model VARCHAR,
  gtin VARCHAR,
  category VARCHAR,
  locale VARCHAR,
  country VARCHAR,
  priority INT NOT NULL,
  attempts INT NOT NULL,
  max_attempts INT NOT NULL,
  next_run_at VARCHAR NOT NULL,
  last_run_id VARCHAR,
  last_error VARCHAR,
  evidence_json VARCHAR,
  status VARCHAR NOT NULL,
  created_at VARCHAR,
  updated_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_product_ingest_run (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  run_id VARCHAR NOT NULL,
  parent_run_id VARCHAR,
  frontier_vid VARCHAR,
  assistant_id VARCHAR NOT NULL,
  dispatched_run_id VARCHAR,
  input_json VARCHAR,
  result_json VARCHAR,
  status VARCHAR NOT NULL,
  started_at VARCHAR,
  finished_at VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_product_ingest_frontier_ready
  ON vertex_product_ingest_frontier (status, next_run_at, priority);

CREATE INDEX IF NOT EXISTS idx_product_ingest_frontier_url
  ON vertex_product_ingest_frontier (official_url, merchant_url);

CREATE INDEX IF NOT EXISTS idx_product_ingest_frontier_gtin
  ON vertex_product_ingest_frontier (gtin);

CREATE INDEX IF NOT EXISTS idx_product_ingest_run_parent
  ON vertex_product_ingest_run (parent_run_id, status);

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, created_date, sensitivity_ord, owner_did, assistant_id,
   version, kind, factory_path, description, checkpointer_mode, created_at)
SELECT
  'global_product_ingest_resident', 0, DATE '2026-05-09', 0, 'did:web:gtin.gftd.ai',
  'global_product_ingest_resident', 1, 'py_factory',
  'pymagatama.langgraph_graphs.global_product_ingest_resident',
  'Resident bounded dispatcher for global product frontier ingest into global_product_enrich_one.',
  'rw_vertex',
  '2026-05-09T23:30:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_assistant
  WHERE assistant_id = 'global_product_ingest_resident' AND version = 1
);

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, created_date, sensitivity_ord, owner_did, nsid,
   assistant_id, version, status, replicas, updated_at)
SELECT
  'langgraph.builtin.global_product_ingest_resident', 0, DATE '2026-05-09', 0,
  'did:web:gtin.gftd.ai', 'langgraph.builtin.global_product_ingest_resident',
  'global_product_ingest_resident', 1, 'active', 1, '2026-05-09T23:30:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_deployment
  WHERE vertex_id = 'langgraph.builtin.global_product_ingest_resident'
);
