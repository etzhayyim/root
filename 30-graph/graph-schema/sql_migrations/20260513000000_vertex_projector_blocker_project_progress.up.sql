-- vertex_projector_blocker: per-project blocker tracking
CREATE TABLE IF NOT EXISTS vertex_projector_blocker (
  vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
  owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
  project_id VARCHAR,
  blocker_type VARCHAR,
  title VARCHAR,
  description VARCHAR,
  status VARCHAR,
  severity VARCHAR,
  reported_by VARCHAR,
  resolved_by VARCHAR,
  resolved_at VARCHAR,
  created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
);

-- edge_projector_project_dep: project dependency edges (src blocks/depends-on dst)
CREATE TABLE IF NOT EXISTS edge_projector_project_dep (
  edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
  _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
  dep_kind VARCHAR,
  created_at VARCHAR, org_id VARCHAR
);

-- Extend vertex_project_props with lifecycle tracking columns
ALTER TABLE vertex_project_props ADD COLUMN IF NOT EXISTS progress_permille BIGINT DEFAULT 0;
ALTER TABLE vertex_project_props ADD COLUMN IF NOT EXISTS lifecycle_state VARCHAR DEFAULT 'planning';
ALTER TABLE vertex_project_props ADD COLUMN IF NOT EXISTS lg_thread_id VARCHAR;
ALTER TABLE vertex_project_props ADD COLUMN IF NOT EXISTS target_date VARCHAR;
ALTER TABLE vertex_project_props ADD COLUMN IF NOT EXISTS org_id VARCHAR;
ALTER TABLE vertex_project_props ADD COLUMN IF NOT EXISTS user_id VARCHAR;
ALTER TABLE vertex_project_props ADD COLUMN IF NOT EXISTS actor_id VARCHAR;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_projector_blocker_project
  ON vertex_projector_blocker (project_id, status);

CREATE INDEX IF NOT EXISTS idx_projector_project_dep_src
  ON edge_projector_project_dep (src_vid, dep_kind);

CREATE INDEX IF NOT EXISTS idx_projector_project_dep_dst
  ON edge_projector_project_dep (dst_vid);

CREATE INDEX IF NOT EXISTS idx_project_props_lifecycle
  ON vertex_project_props (lifecycle_state, org_id);

-- Materialized view: aggregated project status with blocker counts
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_projector_project_status AS
SELECT
  p.vertex_id,
  p.name,
  p.status,
  p.lifecycle_state,
  p.progress_permille,
  p.target_date,
  p.org_id,
  p.owner_did,
  p.parent_id,
  COUNT(b.vertex_id) FILTER (WHERE b.status = 'open')::bigint AS open_blocker_count,
  COUNT(b.vertex_id)::bigint AS total_blocker_count
FROM vertex_project_props p
LEFT JOIN vertex_projector_blocker b ON b.project_id = p.vertex_id
GROUP BY
  p.vertex_id, p.name, p.status, p.lifecycle_state, p.progress_permille,
  p.target_date, p.org_id, p.owner_did, p.parent_id;
