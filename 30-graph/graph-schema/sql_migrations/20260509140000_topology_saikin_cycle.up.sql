-- Topology migration for saikin.cycle.v1 (P3 PoC, ADR-2605080600).
-- Replaces the py_factory row with a full topology spec + 5 node bindings.
-- vertex_id PK = same assistant_id ('saikin.cycle.v1') so this is a row swap.
-- The watcher detects the change via updated_at diff and re-compiles.
--
-- Behavior preservation:
--   entry: probe → conditional(_has_signals_gate) → {transfer, END}
--   transfer → conditional(_transfer_outcome_gate) → {form_colony, lyse}
--   form_colony → handoff → END
--   lyse → END

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord,
   assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES (
  'saikin.cycle.v1', 0, 0,
  'saikin.cycle.v1', 1, 'topology', NULL,
  '{"state_keys":["signalCount","signals","transferId","transferStatus","signalId","colonyId","memberCount","kiAbsorbId","kiAbsorbVertexId","lysed","releasedAt","ok","error"],"entry":"probe","edges":[{"from":"form_colony","to":"handoff"},{"from":"handoff","to":"END"},{"from":"lyse","to":"END"}],"conditional_edges":[{"from":"probe","router":"pymagatama.langgraph_graphs.saikin_cycle:_has_signals_gate","paths":{"transfer":"transfer","no_signals":"END"}},{"from":"transfer","router":"pymagatama.langgraph_graphs.saikin_cycle:_transfer_outcome_gate","paths":{"form_colony":"form_colony","lyse":"lyse"}}]}',
  'saikin horizontal-transfer cycle (topology, P3)',
  '2026-05-08T18:00:00Z'
);

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  -- ADR-2605082000 §2.5: 5 lines below grandfathered with lint-py-primitive-ok.
  -- Migration target: replace py_primitive refs with mcp_tool / sql_udf bindings
  -- (deps.toml [[migrations]] saikin-cycle-mcp-migration). Do NOT add new
  -- py_primitive rows — see lint-langgraph-py-primitive-ban.
  ('saikin.cycle.v1:probe',       0, 0, 'saikin.cycle.v1', 'probe',
   'py_primitive', 'pymagatama.langgraph_graphs.saikin_cycle:_probe_node',       NULL, '2026-05-08T18:00:00Z'), -- lint-py-primitive-ok
  ('saikin.cycle.v1:transfer',    0, 0, 'saikin.cycle.v1', 'transfer',
   'py_primitive', 'pymagatama.langgraph_graphs.saikin_cycle:_transfer_node',    NULL, '2026-05-08T18:00:00Z'), -- lint-py-primitive-ok
  ('saikin.cycle.v1:form_colony', 0, 0, 'saikin.cycle.v1', 'form_colony',
   'py_primitive', 'pymagatama.langgraph_graphs.saikin_cycle:_form_colony_node', NULL, '2026-05-08T18:00:00Z'), -- lint-py-primitive-ok
  ('saikin.cycle.v1:handoff',     0, 0, 'saikin.cycle.v1', 'handoff',
   'py_primitive', 'pymagatama.langgraph_graphs.saikin_cycle:_handoff_node',     NULL, '2026-05-08T18:00:00Z'), -- lint-py-primitive-ok
  ('saikin.cycle.v1:lyse',        0, 0, 'saikin.cycle.v1', 'lyse',
   'py_primitive', 'pymagatama.langgraph_graphs.saikin_cycle:_lyse_node',        NULL, '2026-05-08T18:00:00Z'); -- lint-py-primitive-ok

-- Bump deployment row's updated_at so the watcher detects the change.
INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at)
VALUES
  ('langgraph.builtin.saikin.cycle.v1', 0, 0,
   'langgraph.builtin.saikin.cycle.v1', 'saikin.cycle.v1', 1, 'active', 1,
   '2026-05-08T18:00:00Z');
