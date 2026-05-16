UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'copyright_ingest';

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = 'copyright_ingest.v2';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id = 'copyright_ingest.v2';
DELETE FROM vertex_mcp_tool_def
 WHERE nsid IN (
   'ai.gftd.apps.copyright.fetchCrossref',
   'ai.gftd.apps.copyright.insertCrossref',
   'ai.gftd.apps.copyright.fetchDatacite',
   'ai.gftd.apps.copyright.insertDatacite'
 );

FLUSH;
