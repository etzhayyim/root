-- Revert saikin.cycle.v1 to py_factory.
INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES (
  'saikin.cycle.v1', 0, 0, 'saikin.cycle.v1', 1, 'py_factory',
  'pymagatama.langgraph_graphs.saikin_cycle', NULL,
  'auto-seeded P1a', '2026-05-08T16:00:00Z'
);

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id='saikin.cycle.v1';
