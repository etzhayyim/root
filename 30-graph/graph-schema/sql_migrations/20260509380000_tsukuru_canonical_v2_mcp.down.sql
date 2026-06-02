UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'tsukuru_isic_pulse';

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = 'tsukuru_isic_pulse.v2';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id = 'tsukuru_isic_pulse.v2';
DELETE FROM vertex_mcp_tool_def             WHERE nsid = 'com.etzhayyim.apps.tsukuru.selectManufacturers';

FLUSH;
