-- ADR-2605082000 Phase A — koke canonical migration (saikin/ki sibling).
--
-- Bulk-51 koke.cycle.v1: 5 py_primitive nodes + 2 conditional routers
-- (Python). v2 binds each node to mcp://com.etzhayyim.apps.koke.<method> with
-- the canonical method names matching pymagatama.koke_worker_main:
-- task_<snake> (no `task_koke_` prefix).
--
-- Structure preserved:
--   scan → router(_has_signals_gate) → {fix | END}
--   fix → classify → router(_confidence_gate) → {handoff_hakkou | handoff_saikin}
--   handoff_hakkou → END
--   handoff_saikin → END
-- Conditional routers stay Python (Phase 2 Rego/DMN follow-up).

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:koke.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-koke-scanRawSignals',
   0, 0, 'com.etzhayyim.apps.koke.scanRawSignals', 'did:web:koke.etzhayyim.com', 'koke.etzhayyim.com', 'procedure',
   'koke scan raw signals (primary fixation layer).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/koke/scanRawSignals.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:koke.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-koke-fixSignal',
   0, 0, 'com.etzhayyim.apps.koke.fixSignal', 'did:web:koke.etzhayyim.com', 'koke.etzhayyim.com', 'procedure',
   'koke fix raw signal into a fixation.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/koke/fixSignal.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:koke.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-koke-classifyFixation',
   0, 0, 'com.etzhayyim.apps.koke.classifyFixation', 'did:web:koke.etzhayyim.com', 'koke.etzhayyim.com', 'procedure',
   'koke classify fixation kind / confidence.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/koke/classifyFixation.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:koke.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-koke-handoffToHakkou',
   0, 0, 'com.etzhayyim.apps.koke.handoffToHakkou', 'did:web:koke.etzhayyim.com', 'koke.etzhayyim.com', 'procedure',
   'koke handoff to hakkou (high-confidence fermentation layer).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/koke/handoffToHakkou.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:koke.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-koke-handoffToSaikin',
   0, 0, 'com.etzhayyim.apps.koke.handoffToSaikin', 'did:web:koke.etzhayyim.com', 'koke.etzhayyim.com', 'procedure',
   'koke handoff to saikin (low-confidence horizontal-transfer layer).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/koke/handoffToSaikin.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('koke.cycle.v2', 0, 0, 'koke.cycle.v2', 2, 'topology', NULL,
   '{"state_keys":["scanOut","fixOut","classifyOut","hakkouOut","saikinOut","ok","error"],"entry":"scan","edges":[{"from":"fix","to":"classify"},{"from":"handoff_hakkou","to":"END"},{"from":"handoff_saikin","to":"END"}],"conditional_edges":[{"from":"scan","router":"pymagatama.langgraph_graphs.koke_cycle:_has_signals_gate","paths":{"fix":"fix","no_signals":"END"}},{"from":"classify","router":"pymagatama.langgraph_graphs.koke_cycle:_confidence_gate","paths":{"hakkou":"handoff_hakkou","saikin":"handoff_saikin"}}]}',
   'koke primary-fixation cycle (topology v2, mcp_tool nodes + conditional routers)',
   '2026-05-09T00:00:00Z', 'rw_vertex', 'did:web:agent.koke.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('koke.cycle.v2:scan', 0, 0, 'koke.cycle.v2', 'scan',
   'mcp_tool', 'mcp://com.etzhayyim.apps.koke.scanRawSignals',
   '{"input_keys":[],"result_key":"scanOut","args":{"name":"com.etzhayyim.apps.koke.scanRawSignals"}}',
   '2026-05-09T00:00:00Z'),
  ('koke.cycle.v2:fix', 0, 0, 'koke.cycle.v2', 'fix',
   'mcp_tool', 'mcp://com.etzhayyim.apps.koke.fixSignal',
   '{"input_keys":[],"result_key":"fixOut","args":{"name":"com.etzhayyim.apps.koke.fixSignal"}}',
   '2026-05-09T00:00:00Z'),
  ('koke.cycle.v2:classify', 0, 0, 'koke.cycle.v2', 'classify',
   'mcp_tool', 'mcp://com.etzhayyim.apps.koke.classifyFixation',
   '{"input_keys":[],"result_key":"classifyOut","args":{"name":"com.etzhayyim.apps.koke.classifyFixation"}}',
   '2026-05-09T00:00:00Z'),
  ('koke.cycle.v2:handoff_hakkou', 0, 0, 'koke.cycle.v2', 'handoff_hakkou',
   'mcp_tool', 'mcp://com.etzhayyim.apps.koke.handoffToHakkou',
   '{"input_keys":[],"result_key":"hakkouOut","args":{"name":"com.etzhayyim.apps.koke.handoffToHakkou"}}',
   '2026-05-09T00:00:00Z'),
  ('koke.cycle.v2:handoff_saikin', 0, 0, 'koke.cycle.v2', 'handoff_saikin',
   'mcp_tool', 'mcp://com.etzhayyim.apps.koke.handoffToSaikin',
   '{"input_keys":[],"result_key":"saikinOut","args":{"name":"com.etzhayyim.apps.koke.handoffToSaikin"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'koke.cycle.v2'
 WHERE assistant_id = 'koke.cycle.v1';

FLUSH;
