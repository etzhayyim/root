DROP INDEX IF EXISTS idx_edge_risingwave_operation_dep_dst;

DROP INDEX IF EXISTS idx_edge_risingwave_operation_dep_src;

DROP INDEX IF EXISTS idx_vertex_risingwave_operation_kind;

DROP INDEX IF EXISTS idx_vertex_risingwave_operation_status;

DROP TABLE IF EXISTS edge_risingwave_operation_depends_on;

DROP TABLE IF EXISTS vertex_risingwave_operation;
