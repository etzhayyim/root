DROP MATERIALIZED VIEW IF EXISTS mv_telecom_submarine_cable_capacity;
DROP MATERIALIZED VIEW IF EXISTS mv_telecom_wlan_mesh_link_state;
DROP MATERIALIZED VIEW IF EXISTS mv_telecom_bluetooth_inventory;

DROP TABLE IF EXISTS edge_telecom_submarine_segment_connects_station;
DROP TABLE IF EXISTS edge_telecom_wlan_mesh_link_between_nodes;
DROP TABLE IF EXISTS edge_telecom_bluetooth_mesh_neighbor;

DROP TABLE IF EXISTS vertex_telecom_submarine_repair_event;
DROP TABLE IF EXISTS vertex_telecom_submarine_route_segment;
DROP TABLE IF EXISTS vertex_telecom_submarine_repeater;
DROP TABLE IF EXISTS vertex_telecom_submarine_landing_station;
DROP TABLE IF EXISTS vertex_telecom_submarine_cable_system;
DROP TABLE IF EXISTS vertex_telecom_wlan_mesh_link;
DROP TABLE IF EXISTS vertex_telecom_wlan_mesh_node;
DROP TABLE IF EXISTS vertex_telecom_bluetooth_observation;
DROP TABLE IF EXISTS vertex_telecom_bluetooth_mesh_node;
DROP TABLE IF EXISTS vertex_telecom_bluetooth_device;
