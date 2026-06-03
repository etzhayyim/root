-- ADR-2605082000 Phase B PoC #3 — copyright_ingest minimal migration.
--
-- bulk-51 v1: fetch_crossref → insert_crossref → fetch_datacite →
--             insert_datacite → emit_audit → END  (5 nodes, all py_primitive)
--
-- v2: emit_audit → tools.audit.emit (1 node data-resolved)
--     Other 4 nodes grandfathered (httpx fetch + sa_executemany INSERT
--     don't fit current generic primitives — http.fetch is single-call,
--     no INSERT primitive yet).
--
-- This is the minimum-effort half-measure: 1/5 nodes migrated. The
-- alternative (full migration) requires a `tools.sql.exec` primitive
-- with strict guard for write SQL — Phase C scope.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-fetchCrossref',
   0, 0, 'com.etzhayyim.apps.copyright.fetchCrossref', 'did:web:copyright.etzhayyim.com', 'copyright.etzhayyim.com', 'procedure',
   'copyright fetch Crossref (shelf-stocked, py_primitive grandfather in v2).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/copyright/fetchCrossref.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-insertCrossref',
   0, 0, 'com.etzhayyim.apps.copyright.insertCrossref', 'did:web:copyright.etzhayyim.com', 'copyright.etzhayyim.com', 'procedure',
   'copyright insert Crossref rows (shelf-stocked).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/copyright/insertCrossref.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-fetchDatacite',
   0, 0, 'com.etzhayyim.apps.copyright.fetchDatacite', 'did:web:copyright.etzhayyim.com', 'copyright.etzhayyim.com', 'procedure',
   'copyright fetch DataCite (shelf-stocked).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/copyright/fetchDatacite.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-insertDatacite',
   0, 0, 'com.etzhayyim.apps.copyright.insertDatacite', 'did:web:copyright.etzhayyim.com', 'copyright.etzhayyim.com', 'procedure',
   'copyright insert DataCite rows (shelf-stocked).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/copyright/insertDatacite.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('copyright_ingest.v2', 0, 0, 'copyright_ingest.v2', 2, 'topology', NULL,
   '{"state_keys":["crossrefItems","dataciteItems","crossrefRows","dataciteRows","auditOut","crossrefError","dataciteError","ok","error"],"entry":"fetch_crossref","edges":[{"from":"fetch_crossref","to":"insert_crossref"},{"from":"insert_crossref","to":"fetch_datacite"},{"from":"fetch_datacite","to":"insert_datacite"},{"from":"insert_datacite","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}',
   'copyright ingest (topology v2, 1/5 mcp_tool + 4 grandfather)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.copyright.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('copyright_ingest.v2:fetch_crossref', 0, 0, 'copyright_ingest.v2', 'fetch_crossref',
   'py_primitive', 'pymagatama.langgraph_graphs.copyright_ingest:fetch_crossref', NULL, '2026-05-09T00:00:00Z'), -- lint-py-primitive-ok
  ('copyright_ingest.v2:insert_crossref', 0, 0, 'copyright_ingest.v2', 'insert_crossref',
   'py_primitive', 'pymagatama.langgraph_graphs.copyright_ingest:insert_crossref', NULL, '2026-05-09T00:00:00Z'), -- lint-py-primitive-ok
  ('copyright_ingest.v2:fetch_datacite', 0, 0, 'copyright_ingest.v2', 'fetch_datacite',
   'py_primitive', 'pymagatama.langgraph_graphs.copyright_ingest:fetch_datacite', NULL, '2026-05-09T00:00:00Z'), -- lint-py-primitive-ok
  ('copyright_ingest.v2:insert_datacite', 0, 0, 'copyright_ingest.v2', 'insert_datacite',
   'py_primitive', 'pymagatama.langgraph_graphs.copyright_ingest:insert_datacite', NULL, '2026-05-09T00:00:00Z'), -- lint-py-primitive-ok
  ('copyright_ingest.v2:emit_audit', 0, 0, 'copyright_ingest.v2', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:copyright.etzhayyim.com","collection":"com.etzhayyim.apps.copyright.audit","action":"ingest"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'copyright_ingest.v2'
 WHERE assistant_id = 'copyright_ingest';

FLUSH;
