DROP MATERIALIZED VIEW IF EXISTS mv_maps_active_alerts;

DROP MATERIALIZED VIEW IF EXISTS mv_maps_recent_trip_update;

DROP MATERIALIZED VIEW IF EXISTS mv_maps_recent_vehicle_position;

DROP INDEX IF EXISTS idx_maps_rt_alert_active;

DROP INDEX IF EXISTS idx_maps_rt_tu_trip_stop;

DROP INDEX IF EXISTS idx_maps_rt_vp_feed_ts;

DROP TABLE IF EXISTS vertex_maps_service_alert;

DROP TABLE IF EXISTS vertex_maps_trip_update;

DROP TABLE IF EXISTS vertex_maps_vehicle_position;
