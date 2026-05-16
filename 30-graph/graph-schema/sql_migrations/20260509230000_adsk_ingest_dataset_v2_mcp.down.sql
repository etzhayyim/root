UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'adsk_ingest_dataset';

DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id = 'adsk_ingest_dataset.v2';

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id = 'adsk_ingest_dataset.v2';

DELETE FROM vertex_mcp_tool_def WHERE vertex_id =
  'at://did:web:adsk.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-apps-adsk-datasetIngestAll';

FLUSH;
