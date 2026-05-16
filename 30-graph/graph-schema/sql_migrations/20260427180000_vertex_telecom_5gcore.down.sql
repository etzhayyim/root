DROP MATERIALIZED VIEW IF EXISTS mv_telecom_auth_failure_rate;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_5g_charging_summary;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_active_sessions;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_nf_topology;

DROP TABLE IF EXISTS edge_telecom_charging_to_subscriber;

DROP TABLE IF EXISTS edge_telecom_charging_for_session;

DROP TABLE IF EXISTS edge_telecom_session_on_node;

DROP TABLE IF EXISTS edge_telecom_session_under_policy;

DROP TABLE IF EXISTS edge_telecom_session_uses_slice;

DROP TABLE IF EXISTS vertex_telecom_charging_record;

DROP TABLE IF EXISTS vertex_telecom_pdu_session;

DROP TABLE IF EXISTS vertex_telecom_policy_decision;

DROP TABLE IF EXISTS vertex_telecom_slice_selection;

DROP TABLE IF EXISTS vertex_telecom_amf_registration;

DROP TABLE IF EXISTS vertex_telecom_auth_event;

DROP TABLE IF EXISTS vertex_telecom_subscriber_profile_5g;

DROP TABLE IF EXISTS vertex_telecom_nf_instance;
