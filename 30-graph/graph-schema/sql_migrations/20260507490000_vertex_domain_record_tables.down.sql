DROP MATERIALIZED VIEW IF EXISTS mv_os_window_state;

DROP MATERIALIZED VIEW IF EXISTS mv_os_budget_balance;

DROP MATERIALIZED VIEW IF EXISTS mv_os_consent_pending;

DROP MATERIALIZED VIEW IF EXISTS mv_os_agent_state;

DROP TABLE IF EXISTS vertex_os_window_event;

DROP TABLE IF EXISTS vertex_os_sync_event;

DROP TABLE IF EXISTS vertex_os_directory_entry;

DROP TABLE IF EXISTS edge_os_budget_agent;

DROP TABLE IF EXISTS vertex_os_budget_allocation;

DROP TABLE IF EXISTS edge_os_consent_response;

DROP TABLE IF EXISTS vertex_os_consent_response;

DROP TABLE IF EXISTS vertex_os_consent_request;

DROP TABLE IF EXISTS edge_os_agent_event;

DROP TABLE IF EXISTS vertex_os_agent_event;

DROP TABLE IF EXISTS vertex_os_agent;

DROP TABLE IF EXISTS vertex_graph_consume_tick;

DROP TABLE IF EXISTS vertex_pds_operation_tick;

DROP TABLE IF EXISTS vertex_pds_domain_coverage_expansion;

DROP TABLE IF EXISTS vertex_murakumo_record;

DROP TABLE IF EXISTS vertex_magatama_record;

DROP TABLE IF EXISTS vertex_wellbecoming_record;

DROP TABLE IF EXISTS vertex_projector_record;

DROP TABLE IF EXISTS vertex_gov_record;

DROP TABLE IF EXISTS vertex_os_record;

DROP TABLE IF EXISTS vertex_kenkyusha_record;

DROP TABLE IF EXISTS vertex_organizer_record;

DROP TABLE IF EXISTS vertex_handotai_record;
