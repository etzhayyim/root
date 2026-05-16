DROP MATERIALIZED VIEW IF EXISTS mv_flight_operator_kpi_daily;

DROP MATERIALIZED VIEW IF EXISTS mv_flight_operation_latest_by_aircraft;

DROP TABLE IF EXISTS edge_flight_arrives_at;

DROP TABLE IF EXISTS edge_flight_departs_from;

DROP TABLE IF EXISTS edge_flight_operated_by;

DROP TABLE IF EXISTS edge_flight_uses_aircraft;

DROP TABLE IF EXISTS edge_aircraft_operated_by;

DROP TABLE IF EXISTS edge_aircraft_owned_by;

DROP TABLE IF EXISTS vertex_flight_operation;

DROP TABLE IF EXISTS vertex_aircraft;
