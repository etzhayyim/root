DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_anomaly_recent;

DROP INDEX IF EXISTS idx_resource_flow_anomaly_severity;

DROP INDEX IF EXISTS idx_resource_flow_anomaly_source;

DROP INDEX IF EXISTS idx_resource_flow_anomaly_run;

DROP TABLE IF EXISTS vertex_resource_flow_anomaly;

FLUSH;
