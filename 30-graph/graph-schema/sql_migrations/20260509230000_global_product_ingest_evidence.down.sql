DELETE FROM vertex_langgraph_deployment
WHERE vertex_id = 'langgraph.builtin.global_product_enrich_one';

DELETE FROM vertex_langgraph_assistant
WHERE assistant_id = 'global_product_enrich_one' AND version = 1;

DROP INDEX IF EXISTS idx_edge_product_brand_owner_src;
DROP INDEX IF EXISTS idx_edge_product_official_src;
DROP INDEX IF EXISTS idx_product_fact_key_field;
DROP INDEX IF EXISTS idx_product_fact_product_field;
DROP INDEX IF EXISTS idx_product_source_page_domain;
DROP INDEX IF EXISTS idx_product_source_page_product;
DROP INDEX IF EXISTS idx_product_source_page_url;

DROP TABLE IF EXISTS edge_product_brand_owner;
DROP TABLE IF EXISTS edge_product_official_source;
DROP TABLE IF EXISTS vertex_product_fact_evidence;
DROP TABLE IF EXISTS vertex_product_source_page;
