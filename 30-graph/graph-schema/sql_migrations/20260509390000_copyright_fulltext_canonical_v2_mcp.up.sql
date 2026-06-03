-- ADR-2605082000 Phase B PoC #2 — copyright_fulltext partial migration.
--
-- bulk-51: query_oa_works → fetch_fulltext → store_blobs → emit_audit → END
--
-- v2:
--   query_oa_works → mcp://com.etzhayyim.tools.sql.query (clean SELECT)
--   fetch_fulltext → py_primitive grandfathered (httpx fetch, refactor needed)
--   store_blobs    → py_primitive grandfathered (sa_executemany INSERT,
--                    needs `tools.sql.exec` primitive — Phase C scope)
--   emit_audit     → mcp://com.etzhayyim.tools.audit.emit
--
-- 2/4 nodes data-resolved. The remaining 2 require either Phase B
-- primitive extraction (httpx wrapper, INSERT primitive) or a 5th
-- generic primitive (`tools.http.fetch` / `tools.sql.exec`).

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-queryOaWorks',
   0, 0, 'com.etzhayyim.apps.copyright.queryOaWorks',
   'did:web:copyright.etzhayyim.com', 'copyright.etzhayyim.com', 'procedure',
   'copyright — find Berne-automatic Open Access works lacking blobs.',
   '{"type":"object","properties":{"batchSize":{"type":"integer"}}}',
   '{"type":"object","properties":{"rows":{"type":"array"},"rowCount":{"type":"integer"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/copyright/queryOaWorks.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('copyright_fulltext.v2', 0, 0, 'copyright_fulltext.v2', 2, 'topology', NULL,
   '{"state_keys":["batchSize","queryOut","worksFetched","blobsStored","auditOut","ok","error"],"entry":"query_oa_works","edges":[{"from":"query_oa_works","to":"fetch_fulltext"},{"from":"fetch_fulltext","to":"store_blobs"},{"from":"store_blobs","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}',
   'copyright fulltext (topology v2, 2/4 mcp_tool + 2 grandfather)',
   '2026-05-09T00:00:00Z', 'rw_vertex', 'did:web:agent.copyright.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('copyright_fulltext.v2:query_oa_works', 0, 0, 'copyright_fulltext.v2', 'query_oa_works',
   'mcp_tool', 'mcp://com.etzhayyim.tools.sql.query',
   '{"input_keys":[],"result_key":"queryOut","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT w.vertex_id, w.doi, w.registry FROM vertex_work w WHERE w.berne_automatic = true AND w.doi IS NOT NULL AND NOT EXISTS (SELECT 1 FROM vertex_work_blob wb WHERE wb.work_vertex_id = w.vertex_id) LIMIT 50"}}',
   '2026-05-09T00:00:00Z'),
  -- grandfathered: httpx fetch (no generic primitive yet)
  ('copyright_fulltext.v2:fetch_fulltext', 0, 0, 'copyright_fulltext.v2', 'fetch_fulltext',
   'py_primitive', 'pymagatama.langgraph_graphs.copyright_fulltext:fetch_fulltext', NULL, '2026-05-09T00:00:00Z'), -- lint-py-primitive-ok
  -- grandfathered: sa_executemany INSERT (no generic primitive yet)
  ('copyright_fulltext.v2:store_blobs', 0, 0, 'copyright_fulltext.v2', 'store_blobs',
   'py_primitive', 'pymagatama.langgraph_graphs.copyright_fulltext:store_blobs', NULL, '2026-05-09T00:00:00Z'), -- lint-py-primitive-ok
  ('copyright_fulltext.v2:emit_audit', 0, 0, 'copyright_fulltext.v2', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:copyright.etzhayyim.com","collection":"com.etzhayyim.apps.copyright.audit","action":"fulltext"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'copyright_fulltext.v2'
 WHERE assistant_id = 'copyright_fulltext';

FLUSH;
