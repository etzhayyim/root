-- ADR-2605080000 / ADR-2604251830 — codebase analysis as graph data.
--
-- 3 vertex tables + 2 edge tables + 2 MVs to capture surveys like
-- "how is langchain/langgraph used here?" as queryable graph state.
-- Designed to be reused for any future feature-coverage audit
-- (sqlmesh / pregel / sqlalchemy / pydantic / ...).
--
-- MV memory safety: GROUP BY on low-cardinality keys only
-- (status x layer x ecosystem, expected < 1k distinct keys total).
-- No GROUP BY on file_path, vertex_id, or other high-cardinality columns.

CREATE TABLE IF NOT EXISTS vertex_codebase_analysis (
  vertex_id varchar PRIMARY KEY,
  slug varchar NOT NULL,
  title varchar NOT NULL,
  scope varchar,
  ecosystem varchar,
  performed_by_did varchar,
  performed_at varchar,
  summary varchar,
  doc_uri varchar,
  created_at varchar NOT NULL,
  sensitivity_ord int DEFAULT 100,
  owner_did varchar
);

CREATE TABLE IF NOT EXISTS vertex_codebase_feature (
  vertex_id varchar PRIMARY KEY,
  ecosystem varchar NOT NULL,
  package varchar NOT NULL,
  feature_name varchar NOT NULL,
  feature_kind varchar,
  description varchar,
  upstream_url varchar,
  created_at varchar NOT NULL,
  sensitivity_ord int DEFAULT 0,
  owner_did varchar
);

CREATE TABLE IF NOT EXISTS vertex_codebase_feature_usage (
  vertex_id varchar PRIMARY KEY,
  analysis_vertex_id varchar NOT NULL,
  feature_vertex_id varchar NOT NULL,
  status varchar NOT NULL,
  layer varchar,
  priority varchar,
  role varchar,
  occurrence_count int DEFAULT 0,
  file_paths varchar,
  evidence_note varchar,
  replaced_by_feature_id varchar,
  created_at varchar NOT NULL,
  sensitivity_ord int DEFAULT 100,
  owner_did varchar
);

CREATE TABLE IF NOT EXISTS edge_analysis_covers_feature (
  edge_id varchar PRIMARY KEY,
  src_vid varchar NOT NULL,
  dst_vid varchar NOT NULL,
  edge_kind varchar DEFAULT 'covers',
  created_at varchar NOT NULL,
  sensitivity_ord int DEFAULT 100,
  owner_did varchar
);

CREATE TABLE IF NOT EXISTS edge_feature_replaces (
  edge_id varchar PRIMARY KEY,
  src_vid varchar NOT NULL,
  dst_vid varchar NOT NULL,
  reason varchar,
  created_at varchar NOT NULL,
  sensitivity_ord int DEFAULT 100,
  owner_did varchar
);

CREATE INDEX IF NOT EXISTS idx_codebase_feature_usage_analysis
  ON vertex_codebase_feature_usage (analysis_vertex_id);
CREATE INDEX IF NOT EXISTS idx_codebase_feature_usage_status
  ON vertex_codebase_feature_usage (status, layer);
CREATE INDEX IF NOT EXISTS idx_codebase_feature_usage_priority
  ON vertex_codebase_feature_usage (priority, status);
CREATE INDEX IF NOT EXISTS idx_codebase_feature_ecosystem
  ON vertex_codebase_feature (ecosystem, package);
CREATE INDEX IF NOT EXISTS idx_edge_analysis_covers_src
  ON edge_analysis_covers_feature (src_vid);
CREATE INDEX IF NOT EXISTS idx_edge_feature_replaces_src
  ON edge_feature_replaces (src_vid);

-- mv_codebase_feature_coverage — counts per ecosystem×status (low cardinality, safe).
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_codebase_feature_coverage AS
  SELECT
    f.ecosystem AS ecosystem,
    u.status    AS status,
    u.layer     AS layer,
    COUNT(*)    AS feature_count
  FROM vertex_codebase_feature_usage u
  JOIN vertex_codebase_feature f ON f.vertex_id = u.feature_vertex_id
  GROUP BY f.ecosystem, u.status, u.layer;

-- mv_codebase_feature_priority_open — backlog of P0/P1/P2 not-yet-used features.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_codebase_feature_priority_open AS
  SELECT
    u.priority AS priority,
    u.layer    AS layer,
    f.ecosystem AS ecosystem,
    COUNT(*)   AS open_count
  FROM vertex_codebase_feature_usage u
  JOIN vertex_codebase_feature f ON f.vertex_id = u.feature_vertex_id
  WHERE u.status IN ('not_used','partial','planned')
    AND u.priority IN ('P0','P1','P2','P3')
  GROUP BY u.priority, u.layer, f.ecosystem;
