DROP MATERIALIZED VIEW IF EXISTS mv_vertex_intel_entity_did_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_smishing_sender_blocklist_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_smishing_threat_detection_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_tenso_transfer_request_count;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_intel_report_count;

DROP TABLE IF EXISTS vertex_smishing_takedown_request;

DROP TABLE IF EXISTS vertex_smishing_phishing_report;

DROP TABLE IF EXISTS vertex_smishing_sender_blocklist;

DROP TABLE IF EXISTS vertex_smishing_url_intel;

DROP TABLE IF EXISTS vertex_smishing_threat_detection;

DROP TABLE IF EXISTS vertex_smishing_sms_message;

DROP TABLE IF EXISTS vertex_tenso_access_control;

DROP TABLE IF EXISTS vertex_tenso_transfer_log;

DROP TABLE IF EXISTS vertex_tenso_file_manifest;

DROP TABLE IF EXISTS vertex_tenso_transfer_request;

DROP TABLE IF EXISTS vertex_intel_inferred_cohort;

DROP TABLE IF EXISTS vertex_intel_inference_chain;

DROP TABLE IF EXISTS vertex_intel_entity_did;

DROP TABLE IF EXISTS vertex_intel_report;
