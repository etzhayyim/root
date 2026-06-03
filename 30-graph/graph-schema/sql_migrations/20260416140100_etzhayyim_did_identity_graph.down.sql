DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_delegation_chain;

DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_actor_score;

DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_org_member_count;

FLUSH;

DROP INDEX IF EXISTS idx_edge_etzhayyim_delegates_to_dst;

DROP INDEX IF EXISTS idx_edge_etzhayyim_member_of_dst;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_controller;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_handle;

DROP INDEX IF EXISTS idx_vertex_etzhayyim_identity_did;

FLUSH;

DROP TABLE IF EXISTS edge_etzhayyim_authenticates;

DROP TABLE IF EXISTS edge_etzhayyim_federation;

DROP TABLE IF EXISTS edge_etzhayyim_delegates_to;

DROP TABLE IF EXISTS edge_etzhayyim_controls;

DROP TABLE IF EXISTS edge_etzhayyim_belongs_to_team;

DROP TABLE IF EXISTS edge_etzhayyim_member_of;

DROP TABLE IF EXISTS vertex_etzhayyim_team;

DROP TABLE IF EXISTS vertex_etzhayyim_org;

DROP TABLE IF EXISTS vertex_etzhayyim_identity;

FLUSH;
