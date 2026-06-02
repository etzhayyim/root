UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id IN (
   'aria_attention_ingest', 'aria_emotion_ingest', 'aria_influence_ingest',
   'aria_market_ingest', 'aria_minimax_sweep', 'aria_money_flow_ingest',
   'aria_request_ingest'
 );

DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id LIKE 'aria_%.v2';

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id LIKE 'aria_%.v2';

DELETE FROM vertex_mcp_tool_def
 WHERE nsid LIKE 'com.etzhayyim.apps.aria.%';

FLUSH;
