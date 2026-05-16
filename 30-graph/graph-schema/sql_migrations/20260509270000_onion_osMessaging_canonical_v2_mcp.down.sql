UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id IN ('onion_crawl_seeds', 'os_messaging_crawl_open_channels');

DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id IN ('onion_crawl_seeds.v2', 'os_messaging_crawl_open_channels.v2');

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id IN ('onion_crawl_seeds.v2', 'os_messaging_crawl_open_channels.v2');

DELETE FROM vertex_mcp_tool_def
 WHERE nsid LIKE 'ai.gftd.apps.onion.%' OR nsid LIKE 'ai.gftd.apps.osMessaging.%';

FLUSH;
