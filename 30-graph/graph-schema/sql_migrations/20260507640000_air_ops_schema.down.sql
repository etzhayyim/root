DROP MATERIALIZED VIEW IF EXISTS mv_air_flight_ops_status;

DROP INDEX IF EXISTS idx_air_ops_notam_location_from;

DROP INDEX IF EXISTS idx_air_ops_notam_id;

DROP INDEX IF EXISTS idx_air_ops_flight_plan_carrier_flight_date;

DROP TABLE IF EXISTS edge_air_dispatch_brief_uses_flight_plan;

DROP TABLE IF EXISTS vertex_air_ops_tech_log;

DROP TABLE IF EXISTS vertex_air_ops_pirep;

DROP TABLE IF EXISTS vertex_air_ops_notam;

DROP TABLE IF EXISTS vertex_air_ops_dispatch_brief;

DROP TABLE IF EXISTS vertex_air_ops_flight_plan;
