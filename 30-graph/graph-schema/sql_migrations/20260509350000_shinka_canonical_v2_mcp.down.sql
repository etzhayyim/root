UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'shinka_cron_tick';

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = 'shinka_cron_tick.v2';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id = 'shinka_cron_tick.v2';
DELETE FROM vertex_mcp_tool_def             WHERE nsid LIKE 'com.etzhayyim.apps.shinka.%';

FLUSH;
