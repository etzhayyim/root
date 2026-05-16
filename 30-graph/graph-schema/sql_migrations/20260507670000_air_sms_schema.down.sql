DROP MATERIALIZED VIEW IF EXISTS mv_air_safety_risk_matrix;

DROP INDEX IF EXISTS idx_air_sms_occurrence_id;

DROP INDEX IF EXISTS idx_air_sms_safety_report_category_severity;

DROP INDEX IF EXISTS idx_air_sms_safety_report_id;

DROP TABLE IF EXISTS edge_air_safety_report_triggers_risk;

DROP TABLE IF EXISTS vertex_air_sms_occurrence;

DROP TABLE IF EXISTS vertex_air_sms_iosa_finding;

DROP TABLE IF EXISTS vertex_air_sms_risk_assessment;

DROP TABLE IF EXISTS vertex_air_sms_safety_report;
