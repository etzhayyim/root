UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id IN ('coverage_gap_bridge', 'yoro_platform_pulse');

DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id IN ('coverage_gap_bridge.v2', 'yoro_platform_pulse.v2');

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id IN ('coverage_gap_bridge.v2', 'yoro_platform_pulse.v2');

DELETE FROM vertex_mcp_tool_def
 WHERE nsid LIKE 'com.etzhayyim.apps.coverageGap.%' OR nsid LIKE 'com.etzhayyim.apps.yoro.%';

FLUSH;
