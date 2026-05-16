UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id IN ('public_malak_crawl_ads', 'patent_ingest_uspto_weekly');

DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id IN ('public_malak_crawl_ads.v2', 'patent_ingest_uspto_weekly.v2');

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id IN ('public_malak_crawl_ads.v2', 'patent_ingest_uspto_weekly.v2');

DELETE FROM vertex_mcp_tool_def
 WHERE nsid LIKE 'ai.gftd.apps.publicMalakAds.%' OR nsid LIKE 'ai.gftd.apps.patent.%';

FLUSH;
