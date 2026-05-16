DROP MATERIALIZED VIEW IF EXISTS mv_telecom_kpi_breach_rate;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_spectrum_utilization;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_site_health;

DROP TABLE IF EXISTS edge_telecom_incident_affects_service;

DROP TABLE IF EXISTS edge_telecom_service_runs_on_node;

DROP TABLE IF EXISTS edge_telecom_asset_installed_at;

DROP TABLE IF EXISTS edge_telecom_node_uses_spectrum;

DROP TABLE IF EXISTS edge_telecom_site_hosts_node;

DROP TABLE IF EXISTS vertex_telecom_kpi_sample;

DROP TABLE IF EXISTS vertex_telecom_rma_case;

DROP TABLE IF EXISTS vertex_telecom_maintenance_window;

DROP TABLE IF EXISTS vertex_telecom_site_incident;

DROP TABLE IF EXISTS vertex_telecom_network_asset;

DROP TABLE IF EXISTS vertex_telecom_ran_node;

DROP TABLE IF EXISTS vertex_telecom_cell_site;

DROP TABLE IF EXISTS vertex_telecom_spectrum_license;
