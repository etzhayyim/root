DROP MATERIALIZED VIEW IF EXISTS mv_smishing_threat_flow;

DROP MATERIALIZED VIEW IF EXISTS mv_smishing_url_risk;

DROP TABLE IF EXISTS edge_smishing_url_ioc;

DROP TABLE IF EXISTS edge_smishing_url_takedown;

DROP TABLE IF EXISTS edge_smishing_url_geo;

DROP TABLE IF EXISTS edge_smishing_threat_url;

DROP TABLE IF EXISTS edge_smishing_sms_threat_detection;

DROP TABLE IF EXISTS vertex_smishing_ioc_indicator;

DROP TABLE IF EXISTS vertex_smishing_geo_intel;
