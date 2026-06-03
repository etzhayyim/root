DROP INDEX IF EXISTS idx_edge_etzhayyim_ownership_parent;

DROP INDEX IF EXISTS idx_edge_etzhayyim_ownership_child;

DROP TABLE IF EXISTS edge_etzhayyim_ownership;

DROP INDEX IF EXISTS idx_edge_etzhayyim_fiscal_flow_stage;

DROP INDEX IF EXISTS idx_edge_etzhayyim_fiscal_flow_to;

DROP INDEX IF EXISTS idx_edge_etzhayyim_fiscal_flow_from;

DROP TABLE IF EXISTS edge_etzhayyim_fiscal_flow;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_beneficial_owner_status;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_beneficial_owner_parent_did;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_beneficial_owner_child_did;

DROP TABLE IF EXISTS vertex_etzhayyim_beneficial_owner;
