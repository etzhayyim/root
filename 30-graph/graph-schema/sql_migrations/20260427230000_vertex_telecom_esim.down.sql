DROP MATERIALIZED VIEW IF EXISTS mv_telecom_esim_audit_recent;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_esim_pending_smds_events;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_esim_active_profiles;

DROP TABLE IF EXISTS edge_telecom_esim_smds_event_for_profile;

DROP TABLE IF EXISTS edge_telecom_esim_profile_on_euicc;

DROP TABLE IF EXISTS vertex_telecom_esim_ownership_transfer;

DROP TABLE IF EXISTS vertex_telecom_esim_audit;

DROP TABLE IF EXISTS vertex_telecom_esim_smds_event;

DROP TABLE IF EXISTS vertex_telecom_esim_profile_op;

DROP TABLE IF EXISTS vertex_telecom_esim_profile;

DROP TABLE IF EXISTS vertex_telecom_esim_euicc;
