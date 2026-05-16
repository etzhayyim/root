UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'koke.cycle.v1';

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = 'koke.cycle.v2';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id = 'koke.cycle.v2';
DELETE FROM vertex_mcp_tool_def             WHERE nsid LIKE 'ai.gftd.apps.koke.%';

FLUSH;
