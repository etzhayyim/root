DROP MATERIALIZED VIEW IF EXISTS mv_port_occupancy_event_counts;

DROP MATERIALIZED VIEW IF EXISTS mv_vessel_flag_counts;

DROP MATERIALIZED VIEW IF EXISTS mv_vessel_latest_position;

DROP TABLE IF EXISTS edge_port_call_event;

DROP TABLE IF EXISTS edge_port_infrastructure;

DROP TABLE IF EXISTS edge_vessel_port_call_endpoint;

DROP TABLE IF EXISTS edge_vessel_owner_link;

DROP TABLE IF EXISTS vertex_port_call_event;

DROP TABLE IF EXISTS vertex_port_terminal;

DROP TABLE IF EXISTS vertex_port_berth;

DROP TABLE IF EXISTS vertex_vessel_owner_link;

DROP TABLE IF EXISTS vertex_vessel_port_call;

DROP TABLE IF EXISTS vertex_vessel_voyage;

DROP TABLE IF EXISTS vertex_vessel_position;

DROP TABLE IF EXISTS vertex_vessel_ship_registry;

DROP TABLE IF EXISTS vertex_vessel_shipowner;

DROP TABLE IF EXISTS vertex_vessel_ship;
