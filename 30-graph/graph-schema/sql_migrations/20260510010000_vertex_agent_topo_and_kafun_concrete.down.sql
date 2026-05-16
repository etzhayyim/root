DROP MATERIALIZED VIEW IF EXISTS mv_kafun_pollen_yoy;
DROP MATERIALIZED VIEW IF EXISTS mv_agent_topo_progress;
DROP MATERIALIZED VIEW IF EXISTS mv_agent_topo_ready;

DROP TABLE IF EXISTS vertex_kafun_pollen_observation;
DROP TABLE IF EXISTS vertex_kafun_forest_unit;
DROP TABLE IF EXISTS vertex_kafun_nursery;

DROP TABLE IF EXISTS edge_agent_topo_concerns;
DROP TABLE IF EXISTS edge_agent_topo_depends;
DROP TABLE IF EXISTS vertex_agent_topo_node;
