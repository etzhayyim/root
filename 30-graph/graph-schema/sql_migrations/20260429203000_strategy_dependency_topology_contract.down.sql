DROP VIEW IF EXISTS view_strategy_dependency_llm_payload;

DROP VIEW IF EXISTS view_strategy_dependency_two_node_cycles;

DROP VIEW IF EXISTS view_strategy_dependency_self_cycles;

DROP VIEW IF EXISTS view_strategy_dependency_dangling_edges;

DROP MATERIALIZED VIEW IF EXISTS mv_strategy_dependency_degree;

DROP VIEW IF EXISTS view_strategy_dependency_edge_contract;

DROP VIEW IF EXISTS view_strategy_dependency_known_vertex;

DROP INDEX IF EXISTS idx_dep_topology_order_cycle;

DROP INDEX IF EXISTS idx_dep_topology_order_scope_topo;

DROP INDEX IF EXISTS idx_dep_topology_order_scope_reverse;

DROP TABLE IF EXISTS vertex_dependency_topology_order;
