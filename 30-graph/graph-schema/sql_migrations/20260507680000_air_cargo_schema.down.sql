DROP MATERIALIZED VIEW IF EXISTS mv_air_cargo_revenue;

DROP INDEX IF EXISTS idx_air_cargo_booking_flight_date;

DROP INDEX IF EXISTS idx_air_cargo_uld_no;

DROP INDEX IF EXISTS idx_air_cargo_awb_no;

DROP TABLE IF EXISTS edge_air_awb_loaded_in_uld;

DROP TABLE IF EXISTS vertex_air_cargo_cass_settlement;

DROP TABLE IF EXISTS vertex_air_cargo_claim;

DROP TABLE IF EXISTS vertex_air_cargo_booking;

DROP TABLE IF EXISTS vertex_air_cargo_uld;

DROP TABLE IF EXISTS vertex_air_cargo_awb;
