INSERT INTO vertex_langgraph_assistant (
  vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at
) VALUES (
  'generic_bpmn_runner_graph', 0, 0, 'generic_bpmn_runner_graph', 1, 'py_factory',
  'pymagatama.langgraph_graphs.generic_bpmn_runner', NULL,
  'Generic SpiffWorkflow embedded runner for BPMN (Phase 4)', '2026-05-12T00:00:00Z'
);

INSERT INTO vertex_langgraph_deployment (
  vertex_id, _seq, sensitivity_ord, deployment_id, assistant_id, version, status, updated_at
) VALUES (
  'generic_bpmn_runner_graph:1', 0, 0, 'generic_bpmn_runner_graph:1', 'generic_bpmn_runner_graph', 1, 'active', '2026-05-12T00:00:00Z'
);
