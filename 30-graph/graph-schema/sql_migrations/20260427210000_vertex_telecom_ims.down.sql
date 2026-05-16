DROP MATERIALIZED VIEW IF EXISTS mv_telecom_ims_billing_summary;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_supp_service_usage;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_emergency_routing;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_call_volume;

DROP TABLE IF EXISTS edge_telecom_call_via_interconnect;

DROP TABLE IF EXISTS edge_telecom_call_for_subscriber;

DROP TABLE IF EXISTS edge_telecom_call_uses_session;

DROP TABLE IF EXISTS vertex_telecom_ims_billing_event;

DROP TABLE IF EXISTS vertex_telecom_voice_interconnect_bridge;

DROP TABLE IF EXISTS vertex_telecom_emergency_call;

DROP TABLE IF EXISTS vertex_telecom_supp_service_event;

DROP TABLE IF EXISTS vertex_telecom_voice_call;

DROP TABLE IF EXISTS vertex_telecom_sip_registration;

DROP TABLE IF EXISTS vertex_telecom_ims_subscription;
