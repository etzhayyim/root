UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'shinshi_seed_gap_fill';

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = 'shinshi_seed_gap_fill.v2';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id = 'shinshi_seed_gap_fill.v2';
DELETE FROM vertex_mcp_tool_def             WHERE nsid LIKE 'com.etzhayyim.apps.shinshi.%';

FLUSH;
