-- Reverse of 20260510020000_vertex_keiei_cxo.up.sql

DROP MATERIALIZED VIEW IF EXISTS mv_keiei_role_active_agent;
DROP MATERIALIZED VIEW IF EXISTS mv_keiei_decision_count_by_role;

DROP TABLE IF EXISTS edge_keiei_decision_made_by;
DROP TABLE IF EXISTS edge_keiei_role_has_profile;
DROP TABLE IF EXISTS edge_keiei_reports_to;
DROP TABLE IF EXISTS edge_keiei_agent_acts_as;

DROP TABLE IF EXISTS vertex_keiei_decision;
DROP TABLE IF EXISTS vertex_keiei_profile;
DROP TABLE IF EXISTS vertex_keiei_agent;
DROP TABLE IF EXISTS vertex_keiei_role;

FLUSH;
