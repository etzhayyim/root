-- ADR-2605082000 Phase A — shinshi seed gap fill (conditional + audit).
--
-- Bulk-51 spec:
--   find_incomplete → router(_route_after_find) → {bulk_seed | emit_audit}
--   bulk_seed → emit_audit → END
--   emit_audit → END
--
-- v2 maps:
--   find_incomplete  → mcp://com.etzhayyim.apps.shinshi.coverageFindIncomplete
--   bulk_seed        → mcp://com.etzhayyim.apps.shinshi.sceneBulkSeed
--   emit_audit       → mcp://com.etzhayyim.tools.audit.emit
--
-- Conditional router stays as a Python dotted path (ADR-2605082000 §3
-- Rego/DMN conversion is Phase 2). The 3 shinshi tools register here are:
--   coverageFindIncomplete, sceneBulkSeed, sceneRender (latter is shelf-stocking).
-- Dispatcher entry already wires them via fn_template `task_shinshi_{snake}`
-- against pymagatama.primitives.shinshi_image (iter24).

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:shinshi.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shinshi-coverageFindIncomplete',
   0, 0, 'com.etzhayyim.apps.shinshi.coverageFindIncomplete', 'did:web:shinshi.etzhayyim.com', 'shinshi.etzhayyim.com', 'procedure',
   'shinshi find slugs with incomplete scene coverage.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shinshi/coverageFindIncomplete.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shinshi.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shinshi-sceneBulkSeed',
   0, 0, 'com.etzhayyim.apps.shinshi.sceneBulkSeed', 'did:web:shinshi.etzhayyim.com', 'shinshi.etzhayyim.com', 'procedure',
   'shinshi bulk-seed scenes for incomplete slugs.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shinshi/sceneBulkSeed.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shinshi.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shinshi-sceneRender',
   0, 0, 'com.etzhayyim.apps.shinshi.sceneRender', 'did:web:shinshi.etzhayyim.com', 'shinshi.etzhayyim.com', 'procedure',
   'shinshi scene render (shelf-stocked).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shinshi/sceneRender.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('shinshi_seed_gap_fill.v2', 0, 0, 'shinshi_seed_gap_fill.v2', 2, 'topology', NULL,
   '{"state_keys":["findOut","seedOut","auditOut","ok","error"],"entry":"find_incomplete","edges":[{"from":"bulk_seed","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"find_incomplete","router":"pymagatama.langgraph_graphs.shinshi_seed_gap_fill:_route_after_find","paths":{"bulk_seed":"bulk_seed","emit_audit":"emit_audit"}}]}',
   'shinshi seed gap fill (topology v2, mcp_tool + audit.emit + conditional)',
   '2026-05-09T00:00:00Z', 'rw_vertex', 'did:web:agent.shinshi.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('shinshi_seed_gap_fill.v2:find_incomplete', 0, 0, 'shinshi_seed_gap_fill.v2', 'find_incomplete',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shinshi.coverageFindIncomplete',
   '{"input_keys":[],"result_key":"findOut","args":{"name":"com.etzhayyim.apps.shinshi.coverageFindIncomplete"}}',
   '2026-05-09T00:00:00Z'),
  ('shinshi_seed_gap_fill.v2:bulk_seed', 0, 0, 'shinshi_seed_gap_fill.v2', 'bulk_seed',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shinshi.sceneBulkSeed',
   '{"input_keys":["slugs"],"result_key":"seedOut","args":{"name":"com.etzhayyim.apps.shinshi.sceneBulkSeed"}}',
   '2026-05-09T00:00:00Z'),
  ('shinshi_seed_gap_fill.v2:emit_audit', 0, 0, 'shinshi_seed_gap_fill.v2', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:shinshi.etzhayyim.com","collection":"com.etzhayyim.apps.shinshi.audit","action":"seed_gap_fill"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'shinshi_seed_gap_fill.v2'
 WHERE assistant_id = 'shinshi_seed_gap_fill';

FLUSH;
