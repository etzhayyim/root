-- ADR-2605082000 PoC — saikin.cycle.v2 with kind=mcp_tool nodes.
--
-- Replaces saikin.cycle.v1's 5 py_primitive node bindings with mcp_tool
-- bindings that resolve via vertex_mcp_tool_def (seeded by migration
-- r_20260509160000). v1 is left in place for rollback; the deployment row
-- is flipped to v2.
--
-- Behaviour preservation: spec is identical to v1 (state_keys, entry, edges,
-- conditional_edges). Only the kind/ref/config of each node row changes.
-- Each node:
--   ref    = mcp://com.etzhayyim.apps.saikin.<method>
--   config = { input_keys: [...], result_key: <state_field>,
--              args: { name: "<nsid>" } }
--
-- The output_mapping is implicit: make_mcp_tool_node writes the entire
-- response under config.result_key. Per-field unpacking happens downstream
-- (the original _probe_node etc. flattened a few keys; v2 flattens at
-- consumption time, with the gates still reading state["signalCount"]).
--
-- Runtime caveat: this is a PoC. The saikin Worker today proxies XRPC to
-- a Python dispatcher that does NOT yet handle com.etzhayyim.mcp.message —
-- end-to-end will fail until that wiring is added (deps.toml
-- saikin-cycle-mcp-migration §2). Until then, keep v1 deployed.

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord,
   assistant_id, version, kind, factory_path, spec, description, created_at,
   checkpointer_mode, authored_by)
VALUES (
  'saikin.cycle.v2', 0, 0,
  'saikin.cycle.v2', 2, 'topology', NULL,
  '{"state_keys":["signalCount","signals","probeOut","transferOut","formColonyOut","handoffOut","lyseOut","signalId","colonyId","ok","error"],"entry":"probe","edges":[{"from":"form_colony","to":"handoff"},{"from":"handoff","to":"END"},{"from":"lyse","to":"END"}],"conditional_edges":[{"from":"probe","router":"pymagatama.langgraph_graphs.saikin_cycle:_has_signals_gate","paths":{"transfer":"transfer","no_signals":"END"}},{"from":"transfer","router":"pymagatama.langgraph_graphs.saikin_cycle:_transfer_outcome_gate","paths":{"form_colony":"form_colony","lyse":"lyse"}}]}',
  'saikin horizontal-transfer cycle (topology v2, mcp_tool nodes)',
  '2026-05-09T00:00:00Z',
  'rw_vertex',
  'did:web:agent.saikin.etzhayyim.com'
);

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('saikin.cycle.v2:probe',       0, 0, 'saikin.cycle.v2', 'probe',
   'mcp_tool', 'mcp://com.etzhayyim.apps.saikin.probeEnvironment',
   '{"input_keys":[],"result_key":"probeOut","args":{"name":"com.etzhayyim.apps.saikin.probeEnvironment"}}',
   '2026-05-09T00:00:00Z'),
  ('saikin.cycle.v2:transfer',    0, 0, 'saikin.cycle.v2', 'transfer',
   'mcp_tool', 'mcp://com.etzhayyim.apps.saikin.transferSignal',
   '{"input_keys":["signals"],"result_key":"transferOut","args":{"name":"com.etzhayyim.apps.saikin.transferSignal"}}',
   '2026-05-09T00:00:00Z'),
  ('saikin.cycle.v2:form_colony', 0, 0, 'saikin.cycle.v2', 'form_colony',
   'mcp_tool', 'mcp://com.etzhayyim.apps.saikin.formColony',
   '{"input_keys":["signals"],"result_key":"formColonyOut","args":{"name":"com.etzhayyim.apps.saikin.formColony"}}',
   '2026-05-09T00:00:00Z'),
  ('saikin.cycle.v2:handoff',     0, 0, 'saikin.cycle.v2', 'handoff',
   'mcp_tool', 'mcp://com.etzhayyim.apps.saikin.handoffToKi',
   '{"input_keys":["colonyId","signalId"],"result_key":"handoffOut","args":{"name":"com.etzhayyim.apps.saikin.handoffToKi"}}',
   '2026-05-09T00:00:00Z'),
  ('saikin.cycle.v2:lyse',        0, 0, 'saikin.cycle.v2', 'lyse',
   'mcp_tool', 'mcp://com.etzhayyim.apps.saikin.lyse',
   '{"input_keys":["signalId"],"result_key":"lyseOut","args":{"name":"com.etzhayyim.apps.saikin.lyse"}}',
   '2026-05-09T00:00:00Z');

-- Mark v1 as superseded by v2 (lineage trace per ADR-2605082000 §1).
UPDATE vertex_langgraph_assistant
   SET superseded_by = 'saikin.cycle.v2'
 WHERE assistant_id = 'saikin.cycle.v1';

-- DO NOT flip the deployment pin yet — saikin dispatcher must handle MCP
-- envelopes first. When ready, run:
--   INSERT INTO vertex_langgraph_deployment
--     (vertex_id, nsid, assistant_id, version, status, replicas, updated_at)
--   VALUES ('langgraph.builtin.saikin.cycle.v1',
--           'langgraph.builtin.saikin.cycle.v1', 'saikin.cycle.v2', 2,
--           'active', 1, '2026-05-09T00:00:00Z');

FLUSH;
