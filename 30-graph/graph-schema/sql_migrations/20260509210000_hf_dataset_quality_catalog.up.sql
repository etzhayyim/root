CREATE TABLE IF NOT EXISTS vertex_hf_dataset_collection (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  collection_id VARCHAR NOT NULL,
  display_name VARCHAR,
  purpose VARCHAR,
  selection_policy VARCHAR,
  target_model_scope VARCHAR,
  status VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE TABLE IF NOT EXISTS vertex_hf_dataset_reliability (
  vertex_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  repo_id VARCHAR NOT NULL,
  hf_dataset_vertex_id VARCHAR,
  hfhub_dataset_vertex_id VARCHAR,
  primary_modality VARCHAR,
  training_stage VARCHAR,
  recommended_role VARCHAR,
  license VARCHAR,
  commercial_use VARCHAR,
  artifact_availability VARCHAR,
  text_alignment VARCHAR,
  card_quality_score DOUBLE PRECISION,
  license_score DOUBLE PRECISION,
  availability_score DOUBLE PRECISION,
  alignment_score DOUBLE PRECISION,
  curation_score DOUBLE PRECISION,
  contamination_risk_ord INT,
  pii_risk_ord INT,
  copyright_risk_ord INT,
  eval_leakage_risk_ord INT,
  duplicate_risk_ord INT,
  hub_downloads_month BIGINT,
  hub_likes INT,
  trust_score DOUBLE PRECISION,
  trust_tier VARCHAR,
  decision VARCHAR,
  rationale VARCHAR,
  source_url VARCHAR,
  observed_at VARCHAR,
  status VARCHAR,
  created_at VARCHAR,
  updated_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_hf_dataset_collection_member (
  edge_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  src_vid VARCHAR NOT NULL,
  dst_vid VARCHAR NOT NULL,
  collection_id VARCHAR,
  repo_id VARCHAR,
  primary_modality VARCHAR,
  training_stage VARCHAR,
  rank_in_modality INT,
  required_for_poc BOOLEAN,
  member_status VARCHAR,
  rationale VARCHAR,
  created_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE TABLE IF NOT EXISTS edge_hf_dataset_reliability_about (
  edge_id VARCHAR PRIMARY KEY,
  _seq BIGINT,
  created_date DATE,
  sensitivity_ord INT,
  owner_did VARCHAR,
  src_vid VARCHAR NOT NULL,
  dst_vid VARCHAR NOT NULL,
  repo_id VARCHAR,
  relation_kind VARCHAR,
  confidence DOUBLE PRECISION,
  created_at VARCHAR,
  org_id VARCHAR,
  user_id VARCHAR,
  actor_id VARCHAR
);

CREATE INDEX IF NOT EXISTS idx_hf_dataset_collection_id
  ON vertex_hf_dataset_collection (collection_id);

CREATE INDEX IF NOT EXISTS idx_hf_dataset_reliability_repo
  ON vertex_hf_dataset_reliability (repo_id);

CREATE INDEX IF NOT EXISTS idx_hf_dataset_reliability_modality
  ON vertex_hf_dataset_reliability (primary_modality, training_stage);

CREATE INDEX IF NOT EXISTS idx_hf_dataset_reliability_decision
  ON vertex_hf_dataset_reliability (decision, trust_score);

CREATE INDEX IF NOT EXISTS idx_hf_dataset_collection_member_src
  ON edge_hf_dataset_collection_member (src_vid);

CREATE INDEX IF NOT EXISTS idx_hf_dataset_collection_member_dst
  ON edge_hf_dataset_collection_member (dst_vid);

CREATE INDEX IF NOT EXISTS idx_hf_dataset_collection_member_modality
  ON edge_hf_dataset_collection_member (collection_id, primary_modality, rank_in_modality);

CREATE INDEX IF NOT EXISTS idx_hf_dataset_reliability_about_src
  ON edge_hf_dataset_reliability_about (src_vid);

CREATE INDEX IF NOT EXISTS idx_hf_dataset_reliability_about_dst
  ON edge_hf_dataset_reliability_about (dst_vid);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hf_dataset_quality_top AS
SELECT
  m.collection_id,
  m.primary_modality,
  m.training_stage,
  m.rank_in_modality,
  r.repo_id,
  r.license,
  r.trust_score,
  r.trust_tier,
  r.decision,
  r.commercial_use,
  r.artifact_availability,
  r.text_alignment,
  r.hub_downloads_month,
  r.hub_likes,
  r.source_url,
  r.observed_at
FROM edge_hf_dataset_collection_member m
JOIN vertex_hf_dataset_reliability r
  ON r.vertex_id = m.dst_vid
WHERE m.member_status = 'active'
  AND r.status = 'active'
  AND r.decision IN ('use', 'pilot')
  AND r.trust_score >= 0.70;

GRANT SELECT, INSERT, UPDATE ON vertex_hf_dataset_collection TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_hf_dataset_collection TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON vertex_hf_dataset_reliability TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_hf_dataset_reliability TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON edge_hf_dataset_collection_member TO root;
GRANT SELECT, INSERT, UPDATE ON edge_hf_dataset_collection_member TO kaisya_app;
GRANT SELECT, INSERT, UPDATE ON edge_hf_dataset_reliability_about TO root;
GRANT SELECT, INSERT, UPDATE ON edge_hf_dataset_reliability_about TO kaisya_app;
GRANT SELECT ON mv_hf_dataset_quality_top TO root;
GRANT SELECT ON mv_hf_dataset_quality_top TO kaisya_app;
