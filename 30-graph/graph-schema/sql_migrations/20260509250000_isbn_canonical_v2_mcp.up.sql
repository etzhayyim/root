-- ADR-2605082000 Phase A — isbn canonical-actor consolidation (sibling of aria).
--
-- bulk-51 has 6 isbn_ingest_* assistants (1 node each, all py_primitive,
-- each binding pymagatama.langgraph_graphs.isbn_ingest_<source>:ingest_<source>).
-- This migration:
--   1. Seeds vertex_mcp_tool_def with 6 com.etzhayyim.apps.isbn.* rows pointing at
--      pymagatama.primitives.isbn:task_isbn_<source>_ingest.
--   2. Inserts 6 isbn_ingest_*.v2 assistants with kind=topology + 1 mcp_tool node.
--   3. Marks each bulk-51 v1 as superseded.
--
-- RUNTIME CAVEAT: isbn.etzhayyim.com Worker does NOT exist yet. Same operator
-- guidance as aria/adsk: create Worker (saikin/ki template) or temporarily
-- repoint actor_host to an existing proxy.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:isbn.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-isbn-aozoraIngest',
   0, 0, 'com.etzhayyim.apps.isbn.aozoraIngest', 'did:web:isbn.etzhayyim.com', 'isbn.etzhayyim.com', 'procedure',
   'isbn aozora ingest (Aozora Bunko library catalogue mirror).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/isbn/aozoraIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:isbn.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-isbn-gutenbergIngest',
   0, 0, 'com.etzhayyim.apps.isbn.gutenbergIngest', 'did:web:isbn.etzhayyim.com', 'isbn.etzhayyim.com', 'procedure',
   'isbn Project Gutenberg ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/isbn/gutenbergIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:isbn.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-isbn-hathitrustIngest',
   0, 0, 'com.etzhayyim.apps.isbn.hathitrustIngest', 'did:web:isbn.etzhayyim.com', 'isbn.etzhayyim.com', 'procedure',
   'isbn HathiTrust ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/isbn/hathitrustIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:isbn.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-isbn-internetArchiveIngest',
   0, 0, 'com.etzhayyim.apps.isbn.internetArchiveIngest', 'did:web:isbn.etzhayyim.com', 'isbn.etzhayyim.com', 'procedure',
   'isbn Internet Archive ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/isbn/internetArchiveIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:isbn.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-isbn-ndlIngest',
   0, 0, 'com.etzhayyim.apps.isbn.ndlIngest', 'did:web:isbn.etzhayyim.com', 'isbn.etzhayyim.com', 'procedure',
   'isbn NDL (国立国会図書館) ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/isbn/ndlIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:isbn.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-isbn-openLibraryIngest',
   0, 0, 'com.etzhayyim.apps.isbn.openLibraryIngest', 'did:web:isbn.etzhayyim.com', 'isbn.etzhayyim.com', 'procedure',
   'isbn Open Library ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/isbn/openLibraryIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('isbn_ingest_aozora.v2', 0, 0, 'isbn_ingest_aozora.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"ingest_aozora","edges":[{"from":"ingest_aozora","to":"END"}]}',
   'isbn aozora ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.isbn.etzhayyim.com'),
  ('isbn_ingest_gutenberg.v2', 0, 0, 'isbn_ingest_gutenberg.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"ingest_gutenberg","edges":[{"from":"ingest_gutenberg","to":"END"}]}',
   'isbn gutenberg ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.isbn.etzhayyim.com'),
  ('isbn_ingest_hathitrust.v2', 0, 0, 'isbn_ingest_hathitrust.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"ingest_hathitrust","edges":[{"from":"ingest_hathitrust","to":"END"}]}',
   'isbn hathitrust ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.isbn.etzhayyim.com'),
  ('isbn_ingest_internet_archive.v2', 0, 0, 'isbn_ingest_internet_archive.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"ingest_internet_archive","edges":[{"from":"ingest_internet_archive","to":"END"}]}',
   'isbn internet archive ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.isbn.etzhayyim.com'),
  ('isbn_ingest_ndl.v2', 0, 0, 'isbn_ingest_ndl.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"ingest_ndl","edges":[{"from":"ingest_ndl","to":"END"}]}',
   'isbn NDL ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.isbn.etzhayyim.com'),
  ('isbn_ingest_open_library.v2', 0, 0, 'isbn_ingest_open_library.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"ingest_open_library","edges":[{"from":"ingest_open_library","to":"END"}]}',
   'isbn open library ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.isbn.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('isbn_ingest_aozora.v2:ingest_aozora', 0, 0, 'isbn_ingest_aozora.v2', 'ingest_aozora',
   'mcp_tool', 'mcp://com.etzhayyim.apps.isbn.aozoraIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.isbn.aozoraIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('isbn_ingest_gutenberg.v2:ingest_gutenberg', 0, 0, 'isbn_ingest_gutenberg.v2', 'ingest_gutenberg',
   'mcp_tool', 'mcp://com.etzhayyim.apps.isbn.gutenbergIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.isbn.gutenbergIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('isbn_ingest_hathitrust.v2:ingest_hathitrust', 0, 0, 'isbn_ingest_hathitrust.v2', 'ingest_hathitrust',
   'mcp_tool', 'mcp://com.etzhayyim.apps.isbn.hathitrustIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.isbn.hathitrustIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('isbn_ingest_internet_archive.v2:ingest_internet_archive', 0, 0, 'isbn_ingest_internet_archive.v2', 'ingest_internet_archive',
   'mcp_tool', 'mcp://com.etzhayyim.apps.isbn.internetArchiveIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.isbn.internetArchiveIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('isbn_ingest_ndl.v2:ingest_ndl', 0, 0, 'isbn_ingest_ndl.v2', 'ingest_ndl',
   'mcp_tool', 'mcp://com.etzhayyim.apps.isbn.ndlIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.isbn.ndlIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('isbn_ingest_open_library.v2:ingest_open_library', 0, 0, 'isbn_ingest_open_library.v2', 'ingest_open_library',
   'mcp_tool', 'mcp://com.etzhayyim.apps.isbn.openLibraryIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.isbn.openLibraryIngest"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'isbn_ingest_aozora.v2'           WHERE assistant_id = 'isbn_ingest_aozora';
UPDATE vertex_langgraph_assistant SET superseded_by = 'isbn_ingest_gutenberg.v2'        WHERE assistant_id = 'isbn_ingest_gutenberg';
UPDATE vertex_langgraph_assistant SET superseded_by = 'isbn_ingest_hathitrust.v2'       WHERE assistant_id = 'isbn_ingest_hathitrust';
UPDATE vertex_langgraph_assistant SET superseded_by = 'isbn_ingest_internet_archive.v2' WHERE assistant_id = 'isbn_ingest_internet_archive';
UPDATE vertex_langgraph_assistant SET superseded_by = 'isbn_ingest_ndl.v2'              WHERE assistant_id = 'isbn_ingest_ndl';
UPDATE vertex_langgraph_assistant SET superseded_by = 'isbn_ingest_open_library.v2'     WHERE assistant_id = 'isbn_ingest_open_library';

FLUSH;
