DROP MATERIALIZED VIEW IF EXISTS mv_telecom_ntn_partner_state;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_ntn_contact_throughput;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_ntn_handover_summary;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_ntn_cell_state;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_ntn_earth_station_inventory;

DROP MATERIALIZED VIEW IF EXISTS mv_telecom_ntn_satellite_inventory;

DROP TABLE IF EXISTS edge_telecom_ntn_contact_for_station;

DROP TABLE IF EXISTS edge_telecom_ntn_isl_between_sats;

DROP TABLE IF EXISTS edge_telecom_ntn_handover_for_profile;

DROP TABLE IF EXISTS edge_telecom_ntn_cell_on_satellite;

DROP TABLE IF EXISTS vertex_telecom_ntn_partner;

DROP TABLE IF EXISTS vertex_telecom_ntn_contact;

DROP TABLE IF EXISTS vertex_telecom_ntn_isl;

DROP TABLE IF EXISTS vertex_telecom_ntn_handover;

DROP TABLE IF EXISTS vertex_telecom_ntn_ephemeris;

DROP TABLE IF EXISTS vertex_telecom_ntn_cell;

DROP TABLE IF EXISTS vertex_telecom_ntn_earth_station;

DROP TABLE IF EXISTS vertex_telecom_ntn_satellite;
