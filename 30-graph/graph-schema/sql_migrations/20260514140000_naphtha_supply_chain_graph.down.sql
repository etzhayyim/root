DROP MATERIALIZED VIEW IF EXISTS mv_naphtha_price_latest;
DROP MATERIALIZED VIEW IF EXISTS mv_naphtha_cargo_flow;
DROP MATERIALIZED VIEW IF EXISTS mv_naphtha_country_balance;
DROP MATERIALIZED VIEW IF EXISTS mv_naphtha_supply_chain_trace;

DROP INDEX IF EXISTS idx_edge_naphtha_derivative_src;
DROP INDEX IF EXISTS idx_edge_naphtha_cargo_route_cargo;
DROP INDEX IF EXISTS idx_edge_naphtha_supply_dst;
DROP INDEX IF EXISTS idx_edge_naphtha_supply_src;
DROP INDEX IF EXISTS idx_vertex_naphtha_demand_consumer;
DROP INDEX IF EXISTS idx_vertex_naphtha_price_region_time;
DROP INDEX IF EXISTS idx_vertex_naphtha_cargo_status_grade;
DROP INDEX IF EXISTS idx_vertex_naphtha_cargo_route_ports;
DROP INDEX IF EXISTS idx_vertex_naphtha_market_node_refinery;
DROP INDEX IF EXISTS idx_vertex_naphtha_market_node_kind_country;

DROP TABLE IF EXISTS edge_naphtha_feedstock_to_derivative;
DROP TABLE IF EXISTS edge_naphtha_cargo_route;
DROP TABLE IF EXISTS edge_naphtha_supply_link;
DROP TABLE IF EXISTS vertex_naphtha_cracker_demand;
DROP TABLE IF EXISTS vertex_naphtha_price_assessment;
DROP TABLE IF EXISTS vertex_naphtha_cargo;
DROP TABLE IF EXISTS vertex_naphtha_market_node;
