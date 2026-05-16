DROP MATERIALIZED VIEW IF EXISTS mv_telecom_capacity_breach;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_config_drift;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_change_pipeline;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_alarm_mttr;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_alarm_state;

DROP TABLE IF EXISTS edge_telecom_change_targets_scope;

DROP TABLE IF EXISTS edge_telecom_alarm_correlated_under;

DROP TABLE IF EXISTS edge_telecom_alarm_on_source;

DROP TABLE IF EXISTS vertex_telecom_capacity_forecast;

DROP TABLE IF EXISTS vertex_telecom_config_snapshot;

DROP TABLE IF EXISTS vertex_telecom_change_approval;

DROP TABLE IF EXISTS vertex_telecom_change_request;

DROP TABLE IF EXISTS vertex_telecom_alarm_correlation;

DROP TABLE IF EXISTS vertex_telecom_alarm;
