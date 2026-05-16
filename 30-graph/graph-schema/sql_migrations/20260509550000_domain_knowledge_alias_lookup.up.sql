CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_alias (
  vertex_id VARCHAR PRIMARY KEY,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  game_slug VARCHAR,
  entity_kind VARCHAR,
  entity_vid VARCHAR,
  document_vid VARCHAR,
  chunk_vid VARCHAR,
  alias VARCHAR,
  normalized_alias VARCHAR,
  source VARCHAR,
  score DOUBLE PRECISION,
  created_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS edge_domain_knowledge_alias_of (
  edge_id VARCHAR PRIMARY KEY,
  src_vid VARCHAR,
  dst_vid VARCHAR,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  relation_kind VARCHAR,
  confidence DOUBLE PRECISION,
  created_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_token_index (
  vertex_id VARCHAR PRIMARY KEY,
  created_date DATE,
  sensitivity_ord BIGINT,
  owner_did VARCHAR,
  game_slug VARCHAR,
  entity_kind VARCHAR,
  entity_vid VARCHAR,
  document_vid VARCHAR,
  chunk_vid VARCHAR,
  token VARCHAR,
  token_kind VARCHAR,
  score DOUBLE PRECISION,
  created_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_domain_knowledge_alias_lookup
  ON vertex_domain_knowledge_alias (game_slug, normalized_alias);

CREATE INDEX IF NOT EXISTS idx_domain_knowledge_token_lookup
  ON vertex_domain_knowledge_token_index (game_slug, token);

CREATE INDEX IF NOT EXISTS idx_domain_knowledge_alias_edge_src
  ON edge_domain_knowledge_alias_of (src_vid);
