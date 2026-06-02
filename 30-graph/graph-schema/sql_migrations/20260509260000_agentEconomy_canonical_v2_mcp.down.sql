UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'agent_runtime_lease_autopilot';

DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id = 'agent_runtime_lease_autopilot.v2';

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'agent_runtime_lease_autopilot.v2';

DELETE FROM vertex_mcp_tool_def
 WHERE nsid LIKE 'com.etzhayyim.apps.agentEconomy.%';

FLUSH;
