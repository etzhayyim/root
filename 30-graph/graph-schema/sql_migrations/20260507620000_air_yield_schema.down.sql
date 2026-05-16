DROP MATERIALIZED VIEW IF EXISTS mv_air_revenue_by_route;

DROP INDEX IF EXISTS idx_air_yield_atpco_fare_route;

DROP INDEX IF EXISTS idx_air_yield_fare_class_flight;

DROP TABLE IF EXISTS edge_air_fare_class_references_atpco;

DROP TABLE IF EXISTS vertex_air_yield_demand_forecast;

DROP TABLE IF EXISTS vertex_air_yield_atpco_fare;

DROP TABLE IF EXISTS vertex_air_yield_control;

DROP TABLE IF EXISTS vertex_air_yield_fare_class;
