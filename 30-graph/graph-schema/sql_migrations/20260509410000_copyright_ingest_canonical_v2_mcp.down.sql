UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'copyright_ingest';

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = 'copyright_ingest.v2';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id = 'copyright_ingest.v2';
DELETE FROM vertex_mcp_tool_def
 WHERE nsid IN (
   'com.etzhayyim.apps.copyright.fetchCrossref',
   'com.etzhayyim.apps.copyright.insertCrossref',
   'com.etzhayyim.apps.copyright.fetchDatacite',
   'com.etzhayyim.apps.copyright.insertDatacite'
 );

FLUSH;
