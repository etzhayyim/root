-- ADR-2605082000 Phase B PoC #1 — tsukuru_isic_pulse fully data-resolved
-- via tools.sql.query + tools.audit.emit. First conversion of a
-- "self_logic" actor without per-actor primitive extraction.
--
-- bulk-51 v1: select_manufacturers (sa_query) → emit_audit → END
-- v2:        select_manufacturers via mcp://com.etzhayyim.tools.sql.query
--            (named-param bind on state.industry_codes)
--            emit_audit          via mcp://com.etzhayyim.tools.audit.emit
--
-- Bonus: the v1 SQL used f-string string concat for the IN-list — a
-- silent SQL-injection footgun. v2 uses %(industry_codes)s with array
-- bind (= ANY(...)), which is parameterised at the driver layer.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-tsukuru-selectManufacturers',
   0, 0, 'com.etzhayyim.apps.tsukuru.selectManufacturers',
   'did:web:tsukuru.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'tsukuru ISIC pulse — select manufacturers by industry code (data-bound SQL).',
   '{"type":"object","properties":{"industry_codes":{"type":"array"}}}',
   '{"type":"object","properties":{"rows":{"type":"array"},"rowCount":{"type":"integer"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/tsukuru/selectManufacturers.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('tsukuru_isic_pulse.v2', 0, 0, 'tsukuru_isic_pulse.v2', 2, 'topology', NULL,
   '{"state_keys":["industry_codes","queryOut","auditOut","ok","error"],"entry":"select_manufacturers","edges":[{"from":"select_manufacturers","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}',
   'tsukuru ISIC pulse (topology v2, mcp_tool: tools.sql.query + tools.audit.emit)',
   '2026-05-09T00:00:00Z', 'rw_vertex', 'did:web:agent.tsukuru.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('tsukuru_isic_pulse.v2:select_manufacturers', 0, 0, 'tsukuru_isic_pulse.v2', 'select_manufacturers',
   'mcp_tool', 'mcp://com.etzhayyim.tools.sql.query',
   '{"input_keys":["industry_codes"],"result_key":"queryOut","args":{"name":"com.etzhayyim.tools.sql.query","sql":"SELECT props FROM vertex_other WHERE label = ''TsukuruManufacturer'' AND coalesce(props::jsonb ->> ''industryCode'', '''') = ANY(%(industry_codes)s) LIMIT 25"}}',
   '2026-05-09T00:00:00Z'),
  ('tsukuru_isic_pulse.v2:emit_audit', 0, 0, 'tsukuru_isic_pulse.v2', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:tsukuru.etzhayyim.com","collection":"com.etzhayyim.apps.tsukuru.audit","action":"isic_pulse"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'tsukuru_isic_pulse.v2'
 WHERE assistant_id = 'tsukuru_isic_pulse';

FLUSH;
