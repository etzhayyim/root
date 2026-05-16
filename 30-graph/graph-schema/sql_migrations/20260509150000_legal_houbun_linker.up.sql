CREATE TABLE IF NOT EXISTS vertex_legal_houbun_link_run (
  vertex_id varchar PRIMARY KEY,
  run_id varchar NOT NULL,
  country varchar NOT NULL DEFAULT 'JP',
  jurisdiction varchar NOT NULL DEFAULT 'JPN',
  entity_count bigint NOT NULL DEFAULT 0,
  contract_count bigint NOT NULL DEFAULT 0,
  article_count bigint NOT NULL DEFAULT 0,
  hypothesis_count bigint NOT NULL DEFAULT 0,
  model varchar,
  status varchar NOT NULL DEFAULT 'completed',
  started_at varchar,
  completed_at varchar,
  created_date date,
  sensitivity_ord bigint DEFAULT 0,
  owner_did varchar
);

CREATE TABLE IF NOT EXISTS vertex_legal_houbun_link_hypothesis (
  vertex_id varchar PRIMARY KEY,
  run_id varchar NOT NULL,
  subject_vid varchar NOT NULL,
  subject_kind varchar NOT NULL,
  article_vid varchar NOT NULL,
  relation_type varchar NOT NULL,
  confidence double precision NOT NULL,
  rationale varchar,
  evidence_json varchar,
  status varchar NOT NULL DEFAULT 'pending_review',
  model varchar,
  created_at varchar,
  created_date date,
  sensitivity_ord bigint DEFAULT 0,
  owner_did varchar
);

CREATE TABLE IF NOT EXISTS edge_legal_entity_houbun_article (
  edge_id varchar PRIMARY KEY,
  src_vid varchar NOT NULL,
  dst_vid varchar NOT NULL,
  relation_type varchar NOT NULL,
  confidence double precision NOT NULL,
  hypothesis_vid varchar,
  status varchar NOT NULL DEFAULT 'inferred',
  created_at varchar,
  created_date date,
  sensitivity_ord bigint DEFAULT 0,
  owner_did varchar
);

CREATE TABLE IF NOT EXISTS edge_contract_houbun_article (
  edge_id varchar PRIMARY KEY,
  src_vid varchar NOT NULL,
  dst_vid varchar NOT NULL,
  relation_type varchar NOT NULL,
  confidence double precision NOT NULL,
  hypothesis_vid varchar,
  status varchar NOT NULL DEFAULT 'inferred',
  created_at varchar,
  created_date date,
  sensitivity_ord bigint DEFAULT 0,
  owner_did varchar
);

CREATE INDEX IF NOT EXISTS idx_legal_houbun_hyp_subject ON vertex_legal_houbun_link_hypothesis (subject_vid, status);
CREATE INDEX IF NOT EXISTS idx_legal_houbun_hyp_article ON vertex_legal_houbun_link_hypothesis (article_vid, status);
CREATE INDEX IF NOT EXISTS idx_edge_legal_entity_houbun_src ON edge_legal_entity_houbun_article (src_vid, status);
CREATE INDEX IF NOT EXISTS idx_edge_legal_entity_houbun_dst ON edge_legal_entity_houbun_article (dst_vid, status);
CREATE INDEX IF NOT EXISTS idx_edge_contract_houbun_src ON edge_contract_houbun_article (src_vid, status);
CREATE INDEX IF NOT EXISTS idx_edge_contract_houbun_dst ON edge_contract_houbun_article (dst_vid, status);

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, owner_did, assistant_id, version, kind,
   factory_path, description, created_at)
SELECT
  'legal_houbun_linker', 0, 0, 'did:web:legal-intel.gftd.ai', 'legal_houbun_linker', 1, 'py_factory',
  'pymagatama.langgraph_graphs.legal_houbun_linker',
  'Infer Japanese LEI / contract / houbun article dependency links as reviewable graph hypotheses.',
  '2026-05-09T15:00:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_assistant
  WHERE assistant_id = 'legal_houbun_linker' AND version = 1
);

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, owner_did, nsid, assistant_id,
   version, status, replicas, updated_at)
VALUES
  ('langgraph.builtin.legal_houbun_linker', 0, 0, 'did:web:legal-intel.gftd.ai',
   'langgraph.builtin.legal_houbun_linker', 'legal_houbun_linker', 1, 'active', 1,
   '2026-05-09T15:00:00Z');
