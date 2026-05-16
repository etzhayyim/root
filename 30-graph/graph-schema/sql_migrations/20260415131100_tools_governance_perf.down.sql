DROP MATERIALIZED VIEW IF EXISTS mv_actor_governance_policy;

DROP MATERIALIZED VIEW IF EXISTS mv_actor_tool_grants;

DROP INDEX IF EXISTS idx_edge_governance_src_label_dst;

DROP INDEX IF EXISTS idx_vertex_governance_repo_kind_name;

DROP INDEX IF EXISTS idx_edge_capability_src_label_dst;

DROP INDEX IF EXISTS idx_vertex_capability_collection_status_worker_name;

DROP INDEX IF EXISTS idx_vertex_capability_collection_status_did_name;
