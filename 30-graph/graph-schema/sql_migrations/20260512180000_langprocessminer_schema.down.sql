DROP MATERIALIZED VIEW IF EXISTS mv_lpm_agent_performance_summary;
DROP INDEX IF EXISTS idx_lpm_span_by_trace;
DROP INDEX IF EXISTS idx_lpm_trace_by_agent;
DROP TABLE IF EXISTS edge_langprocessminer_span_hierarchy;
DROP TABLE IF EXISTS vertex_langprocessminer_span;
DROP TABLE IF EXISTS vertex_langprocessminer_trace;

FLUSH;
