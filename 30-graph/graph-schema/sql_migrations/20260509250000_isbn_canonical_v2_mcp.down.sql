UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id IN (
   'isbn_ingest_aozora', 'isbn_ingest_gutenberg', 'isbn_ingest_hathitrust',
   'isbn_ingest_internet_archive', 'isbn_ingest_ndl', 'isbn_ingest_open_library'
 );

DELETE FROM vertex_langgraph_assistant_node
 WHERE assistant_id LIKE 'isbn_ingest_%.v2';

DELETE FROM vertex_langgraph_assistant
 WHERE assistant_id LIKE 'isbn_ingest_%.v2';

DELETE FROM vertex_mcp_tool_def
 WHERE nsid LIKE 'ai.gftd.apps.isbn.%';

FLUSH;
