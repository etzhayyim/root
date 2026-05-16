DELETE FROM vertex_langgraph_deployment
WHERE vertex_id = 'langgraph.builtin.global_product_ingest_resident';

DELETE FROM vertex_langgraph_assistant
WHERE assistant_id = 'global_product_ingest_resident' AND version = 1;

DROP INDEX IF EXISTS idx_product_ingest_run_parent;
DROP INDEX IF EXISTS idx_product_ingest_frontier_gtin;
DROP INDEX IF EXISTS idx_product_ingest_frontier_url;
DROP INDEX IF EXISTS idx_product_ingest_frontier_ready;

DROP TABLE IF EXISTS vertex_product_ingest_run;
DROP TABLE IF EXISTS vertex_product_ingest_frontier;
