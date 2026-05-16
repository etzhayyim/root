UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id = 'copyright_fulltext';

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id = 'copyright_fulltext.v2';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id = 'copyright_fulltext.v2';
DELETE FROM vertex_mcp_tool_def             WHERE nsid = 'ai.gftd.apps.copyright.queryOaWorks';

FLUSH;
