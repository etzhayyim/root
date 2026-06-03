-- ADR-2605082000 Phase B PoC #4 — copyright_ingest v3 full data chain.
--
-- Builds on iter56's e2e_smoke proof: the 4-step
-- (http.fetch → json.extract → transform.map → sql.exec) chain
-- end-to-end-verified in-process. This migration applies the same chain
-- pattern to the Crossref half of copyright_ingest. v2 (iter50) had 1/5
-- nodes data-resolved (emit_audit only); v3 expands to 6/8 (the 2 added
-- intermediate nodes + the original 4 → all chain-resolved).
--
-- v3 graph (Crossref half full + DataCite half grandfather + emit_audit):
--   crossref_fetch     → http.fetch
--   crossref_extract   → json.extract  (path = "message.items")
--   crossref_transform → transform.map (Crossref item → vertex_work row)
--   crossref_insert    → sql.exec      (INSERT INTO vertex_work)
--   datacite_fetch     → py_primitive (grandfather)
--   datacite_insert    → py_primitive (grandfather)
--   emit_audit         → audit.emit
--
-- Notes / simplifications vs v1:
--   - vertex_id format simplified (no _doi_rkey slug — operator should
--     refine the fmt template if rkey shape matters)
--   - `kind` field defaults to "literary" (Python conditional dropped)
--   - `collected_at` omitted (no tools.time.now primitive yet — Phase D)
--   - Defaults / constants reflect _crossref_row Python output shape
--
-- v3 supersedes v2 which superseded v1.

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('copyright_ingest.v3', 0, 0, 'copyright_ingest.v3', 3, 'topology', NULL,
   '{"state_keys":["fetchOut","itemsOut","rowsOut","insertOut","dataciteItems","dataciteRows","auditOut","ok","error"],"entry":"crossref_fetch","edges":[{"from":"crossref_fetch","to":"crossref_extract"},{"from":"crossref_extract","to":"crossref_transform"},{"from":"crossref_transform","to":"crossref_insert"},{"from":"crossref_insert","to":"datacite_fetch"},{"from":"datacite_fetch","to":"datacite_insert"},{"from":"datacite_insert","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}',
   'copyright ingest (topology v3, Crossref half full chain + DataCite grandfather)',
   '2026-05-09T00:00:00Z', 'rw_vertex', 'did:web:agent.copyright.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  -- 1. fetch Crossref API
  ('copyright_ingest.v3:crossref_fetch', 0, 0, 'copyright_ingest.v3', 'crossref_fetch',
   'mcp_tool', 'mcp://com.etzhayyim.tools.http.fetch',
   '{"input_keys":[],"result_key":"fetchOut","args":{"name":"com.etzhayyim.tools.http.fetch","url":"https://api.crossref.org/works?rows=100&sort=indexed&order=desc&filter=from-pub-date%3A2020&mailto=jun%40etzhayyim.group","headers":{"User-Agent":"etzhayyim-copyright/2.0 (mailto:jun@etzhayyim.group)","Accept":"application/json"},"timeout":60}}',
   '2026-05-09T00:00:00Z'),
  -- 2. extract message.items array from fetched body
  ('copyright_ingest.v3:crossref_extract', 0, 0, 'copyright_ingest.v3', 'crossref_extract',
   'mcp_tool', 'mcp://com.etzhayyim.tools.json.extract',
   '{"input_keys":[],"input_paths":{"json":"fetchOut.result.body"},"result_key":"itemsOut","args":{"name":"com.etzhayyim.tools.json.extract","path":"message.items","default":[]}}',
   '2026-05-09T00:00:00Z'),
  -- 3. transform each Crossref item → vertex_work row
  ('copyright_ingest.v3:crossref_transform', 0, 0, 'copyright_ingest.v3', 'crossref_transform',
   'mcp_tool', 'mcp://com.etzhayyim.tools.transform.map',
   '{"input_keys":[],"input_paths":{"input":"itemsOut.result.value"},"result_key":"rowsOut","args":{"name":"com.etzhayyim.tools.transform.map","mapping":{"doi":"$.DOI","title":"$.title[0]","vertex_id":{"fmt":"at://did:web:copyright.etzhayyim.com:crossref/com.etzhayyim.apps.copyright.work/{DOI}"},"source_url":{"fmt":"https://doi.org/{DOI}"}},"defaults":{"owner_did":"did:web:copyright.etzhayyim.com:crossref","repo":"did:web:copyright.etzhayyim.com:crossref","did":"did:web:copyright.etzhayyim.com:crossref","status":"active","kind":"literary","registry":"crossref","berne_automatic":true,"sensitivity_ord":100}}}',
   '2026-05-09T00:00:00Z'),
  -- 4. bulk INSERT into vertex_work
  ('copyright_ingest.v3:crossref_insert', 0, 0, 'copyright_ingest.v3', 'crossref_insert',
   'mcp_tool', 'mcp://com.etzhayyim.tools.sql.exec',
   '{"input_keys":[],"input_paths":{"rows":"rowsOut.result.rows"},"result_key":"insertOut","args":{"name":"com.etzhayyim.tools.sql.exec","sql":"INSERT INTO vertex_work (vertex_id, owner_did, repo, did, status, kind, title, doi, registry, berne_automatic, source_url, sensitivity_ord) VALUES (%(vertex_id)s, %(owner_did)s, %(repo)s, %(did)s, %(status)s, %(kind)s, %(title)s, %(doi)s, %(registry)s, %(berne_automatic)s, %(source_url)s, %(sensitivity_ord)s)","confirmWrite":true}}',
   '2026-05-09T00:00:00Z'),
  -- DataCite half grandfathered (similar full-chain rewrite is operator follow-up)
  ('copyright_ingest.v3:datacite_fetch', 0, 0, 'copyright_ingest.v3', 'datacite_fetch',
   'py_primitive', 'pymagatama.langgraph_graphs.copyright_ingest:fetch_datacite', NULL, '2026-05-09T00:00:00Z'), -- lint-py-primitive-ok
  ('copyright_ingest.v3:datacite_insert', 0, 0, 'copyright_ingest.v3', 'datacite_insert',
   'py_primitive', 'pymagatama.langgraph_graphs.copyright_ingest:insert_datacite', NULL, '2026-05-09T00:00:00Z'), -- lint-py-primitive-ok
  ('copyright_ingest.v3:emit_audit', 0, 0, 'copyright_ingest.v3', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:copyright.etzhayyim.com","collection":"com.etzhayyim.apps.copyright.audit","action":"ingest_v3"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'copyright_ingest.v3'
 WHERE assistant_id = 'copyright_ingest.v2';

FLUSH;
