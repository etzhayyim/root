UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'copyright_ingest.v2';

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = 'copyright_ingest.v3';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id = 'copyright_ingest.v3';

FLUSH;
