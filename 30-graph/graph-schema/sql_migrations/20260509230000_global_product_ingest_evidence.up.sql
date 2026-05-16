CREATE TABLE IF NOT EXISTS vertex_product_source_page (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  source_page_id VARCHAR NOT NULL,
  product_vid VARCHAR,
  product_key VARCHAR,
  source_kind VARCHAR NOT NULL,
  authority_rank INT NOT NULL,
  url VARCHAR NOT NULL,
  domain VARCHAR,
  canonical_url VARCHAR,
  title VARCHAR,
  content_sha256 VARCHAR,
  content_type VARCHAR,
  fetched_at VARCHAR,
  fetch_method VARCHAR,
  http_status INT,
  robots_allowed BOOLEAN,
  evidence_json VARCHAR,
  status VARCHAR NOT NULL,
  created_at VARCHAR,
  updated_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_product_fact_evidence (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  fact_id VARCHAR NOT NULL,
  product_vid VARCHAR,
  product_key VARCHAR,
  source_page_vid VARCHAR,
  source_kind VARCHAR NOT NULL,
  field_name VARCHAR NOT NULL,
  field_value VARCHAR NOT NULL,
  normalized_value VARCHAR,
  extraction_method VARCHAR NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  model VARCHAR,
  prompt_version VARCHAR,
  evidence_json VARCHAR,
  status VARCHAR NOT NULL,
  created_at VARCHAR,
  updated_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_product_official_source (
  edge_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  src_vid VARCHAR NOT NULL,
  dst_vid VARCHAR NOT NULL,
  relation_type VARCHAR NOT NULL,
  source_kind VARCHAR NOT NULL,
  authority_rank INT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  evidence_json VARCHAR,
  status VARCHAR NOT NULL,
  created_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_product_brand_owner (
  edge_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  src_vid VARCHAR NOT NULL,
  dst_vid VARCHAR NOT NULL,
  relation_type VARCHAR NOT NULL,
  brand_name VARCHAR,
  owner_name VARCHAR,
  confidence DOUBLE PRECISION NOT NULL,
  evidence_json VARCHAR,
  status VARCHAR NOT NULL,
  created_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_product_source_page_url
  ON vertex_product_source_page (url);

CREATE INDEX IF NOT EXISTS idx_product_source_page_product
  ON vertex_product_source_page (product_vid, source_kind);

CREATE INDEX IF NOT EXISTS idx_product_source_page_domain
  ON vertex_product_source_page (domain, source_kind);

CREATE INDEX IF NOT EXISTS idx_product_fact_product_field
  ON vertex_product_fact_evidence (product_vid, field_name);

CREATE INDEX IF NOT EXISTS idx_product_fact_key_field
  ON vertex_product_fact_evidence (product_key, field_name);

CREATE INDEX IF NOT EXISTS idx_edge_product_official_src
  ON edge_product_official_source (src_vid, relation_type);

CREATE INDEX IF NOT EXISTS idx_edge_product_brand_owner_src
  ON edge_product_brand_owner (src_vid, relation_type);

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, owner_did, assistant_id, version, kind,
   factory_path, description, checkpointer_mode, created_at)
SELECT
  'global_product_enrich_one', 0, 0, 'did:web:gtin.gftd.ai',
  'global_product_enrich_one', 1, 'py_factory',
  'pymagatama.langgraph_graphs.global_product_enrich_one',
  'Enrich one global product from official pages, merchant pages, webfetch, intel, and inference.',
  'rw_vertex',
  '2026-05-09T23:00:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_assistant
  WHERE assistant_id = 'global_product_enrich_one' AND version = 1
);

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, owner_did, nsid, assistant_id,
   version, status, replicas, updated_at)
SELECT
  'langgraph.builtin.global_product_enrich_one', 0, 0, 'did:web:gtin.gftd.ai',
  'langgraph.builtin.global_product_enrich_one', 'global_product_enrich_one',
  1, 'active', 1, '2026-05-09T23:00:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_deployment
  WHERE vertex_id = 'langgraph.builtin.global_product_enrich_one'
);
