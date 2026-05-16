DROP MATERIALIZED VIEW IF EXISTS mv_agent_role_binding_status;

DROP MATERIALIZED VIEW IF EXISTS mv_state_profile_status;

DROP MATERIALIZED VIEW IF EXISTS mv_yoro_actor_score_counts;

DROP MATERIALIZED VIEW IF EXISTS mv_yoro_actor_evolution_counts;

DROP MATERIALIZED VIEW IF EXISTS mv_yoro_evolution_recent;

DROP MATERIALIZED VIEW IF EXISTS mv_yoro_evolution_stats;

DROP MATERIALIZED VIEW IF EXISTS mv_yoro_browsing_history_recent;

DROP TABLE IF EXISTS edge_agent_governance;

DROP TABLE IF EXISTS edge_state_profile_repo;

DROP TABLE IF EXISTS edge_yoro_actor_score_event;

DROP TABLE IF EXISTS edge_yoro_actor_browsing_history;

DROP TABLE IF EXISTS edge_yoro_actor_evolution;

DROP TABLE IF EXISTS vertex_agent_role_binding;

DROP TABLE IF EXISTS vertex_agent_governance_rule;

DROP TABLE IF EXISTS vertex_state_profile;

DROP TABLE IF EXISTS vertex_joucho_review;

DROP TABLE IF EXISTS vertex_dojo_step_completed_event;

DROP TABLE IF EXISTS vertex_yoro_shinka_knowledge;

DROP TABLE IF EXISTS vertex_yoro_hinshitsu_assessment;

DROP TABLE IF EXISTS vertex_yoro_shinka_evolution;

DROP TABLE IF EXISTS vertex_yoro_kyumei_validation;

DROP TABLE IF EXISTS vertex_yoro_koji_discovery;

DROP TABLE IF EXISTS vertex_yoro_browsing_history;
