DROP MATERIALIZED VIEW IF EXISTS mv_vessel_density_grid;

DROP MATERIALIZED VIEW IF EXISTS mv_vessel_latest_position;

DROP FUNCTION IF EXISTS vessel_flag_iso(bigint);

DROP FUNCTION IF EXISTS vessel_type_class(smallint);

DROP INDEX IF EXISTS idx_vessel_name;

DROP INDEX IF EXISTS idx_vessel_visited_port_locode;

DROP INDEX IF EXISTS idx_vessel_voyage_mmsi;

DROP INDEX IF EXISTS idx_vessel_position_mmsi_ts;

DROP TABLE IF EXISTS edge_vessel_visited_port;

DROP TABLE IF EXISTS vertex_vessel_voyage;

DROP TABLE IF EXISTS vertex_vessel_position;

DROP TABLE IF EXISTS vertex_vessel;
