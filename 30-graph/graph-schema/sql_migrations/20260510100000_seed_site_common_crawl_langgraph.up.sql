INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   description, created_at)
SELECT
  'site_common_crawl_ingest', 0, 0, 'site_common_crawl_ingest', 1, 'py_factory',
  'pymagatama.langgraph_graphs.site_common_crawl_ingest',
  'resident site Common Crawl ingest wrapper',
  '2026-05-10T10:00:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_assistant
  WHERE assistant_id = 'site_common_crawl_ingest'
);

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status,
   replicas, updated_at)
SELECT
  'langgraph.builtin.site_common_crawl_ingest', 0, 0,
  'langgraph.builtin.site_common_crawl_ingest',
  'site_common_crawl_ingest', 1, 'active', 1, '2026-05-10T10:00:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_deployment
  WHERE assistant_id = 'site_common_crawl_ingest'
);
