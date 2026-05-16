DROP MATERIALIZED VIEW IF EXISTS mv_projector_project_status;

DROP INDEX IF EXISTS idx_project_props_lifecycle;
DROP INDEX IF EXISTS idx_projector_project_dep_dst;
DROP INDEX IF EXISTS idx_projector_project_dep_src;
DROP INDEX IF EXISTS idx_projector_blocker_project;

DROP TABLE IF EXISTS edge_projector_project_dep;
DROP TABLE IF EXISTS vertex_projector_blocker;
