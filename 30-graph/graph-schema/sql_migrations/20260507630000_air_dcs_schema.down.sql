DROP MATERIALIZED VIEW IF EXISTS mv_air_turnaround_kpi;

DROP INDEX IF EXISTS idx_air_dcs_checkin_pnr_hash;

DROP INDEX IF EXISTS idx_air_dcs_baggage_tag;

DROP INDEX IF EXISTS idx_air_dcs_checkin_flight_date;

DROP TABLE IF EXISTS edge_air_departure_uses_load_sheet;

DROP TABLE IF EXISTS edge_air_checkin_has_baggage;

DROP TABLE IF EXISTS vertex_air_dcs_departure;

DROP TABLE IF EXISTS vertex_air_dcs_load_sheet;

DROP TABLE IF EXISTS vertex_air_dcs_baggage;

DROP TABLE IF EXISTS vertex_air_dcs_checkin;
