DROP MATERIALIZED VIEW IF EXISTS mv_gftd_delegation_chain;

DROP MATERIALIZED VIEW IF EXISTS mv_gftd_actor_score;

DROP MATERIALIZED VIEW IF EXISTS mv_gftd_org_member_count;

FLUSH;

DROP INDEX IF EXISTS idx_edge_gftd_delegates_to_dst;

DROP INDEX IF EXISTS idx_edge_gftd_member_of_dst;

DROP INDEX IF EXISTS idx_vertex_gftd_identity_controller;

DROP INDEX IF EXISTS idx_vertex_gftd_identity_handle;

DROP INDEX IF EXISTS idx_vertex_gftd_identity_did;

FLUSH;

DROP TABLE IF EXISTS edge_gftd_authenticates;

DROP TABLE IF EXISTS edge_gftd_federation;

DROP TABLE IF EXISTS edge_gftd_delegates_to;

DROP TABLE IF EXISTS edge_gftd_controls;

DROP TABLE IF EXISTS edge_gftd_belongs_to_team;

DROP TABLE IF EXISTS edge_gftd_member_of;

DROP TABLE IF EXISTS vertex_gftd_team;

DROP TABLE IF EXISTS vertex_gftd_org;

DROP TABLE IF EXISTS vertex_gftd_identity;

FLUSH;
