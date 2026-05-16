DROP MATERIALIZED VIEW IF EXISTS mv_resource_flow_anomaly_review_latest;

DROP INDEX IF EXISTS idx_anomaly_review_reviewer;

DROP INDEX IF EXISTS idx_anomaly_review_observed;

DROP INDEX IF EXISTS idx_anomaly_review_anomaly;

DROP TABLE IF EXISTS vertex_resource_flow_anomaly_review;

FLUSH;
