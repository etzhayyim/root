DROP MATERIALIZED VIEW IF EXISTS mv_air_schedule_daily;

DROP INDEX IF EXISTS idx_air_sched_slot_airport_date;

DROP INDEX IF EXISTS idx_air_sched_schedule_origin_dest;

DROP INDEX IF EXISTS idx_air_sched_schedule_carrier_flight;

DROP TABLE IF EXISTS edge_air_schedule_has_slot;

DROP TABLE IF EXISTS edge_air_schedule_uses_route;

DROP TABLE IF EXISTS vertex_air_sched_codeshare;

DROP TABLE IF EXISTS vertex_air_sched_route;

DROP TABLE IF EXISTS vertex_air_sched_slot;

DROP TABLE IF EXISTS vertex_air_sched_schedule;
