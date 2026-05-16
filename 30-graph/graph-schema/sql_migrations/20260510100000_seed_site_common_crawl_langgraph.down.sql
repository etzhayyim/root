DELETE FROM vertex_langgraph_deployment
WHERE assistant_id = 'site_common_crawl_ingest';

DELETE FROM vertex_langgraph_assistant_node
WHERE assistant_id = 'site_common_crawl_ingest';

DELETE FROM vertex_langgraph_assistant
WHERE assistant_id = 'site_common_crawl_ingest';
