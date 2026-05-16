-- Revert 8 single_task rows back to py_factory pointing at _single_task_wrapper.
INSERT INTO vertex_langgraph_assistant (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, description, created_at) VALUES
  ('kobo.budAgent.v1',          0, 0, 'kobo.budAgent.v1',          1, 'py_factory', 'pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kobo_budAgent',          'rollback', '2026-05-08T16:00:00Z'),
  ('kobo.sporulate.v1',         0, 0, 'kobo.sporulate.v1',         1, 'py_factory', 'pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kobo_sporulate',         'rollback', '2026-05-08T16:00:00Z'),
  ('kobo.germinate.v1',         0, 0, 'kobo.germinate.v1',         1, 'py_factory', 'pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kobo_germinate',         'rollback', '2026-05-08T16:00:00Z'),
  ('kabi.fusionProbe.v1',       0, 0, 'kabi.fusionProbe.v1',       1, 'py_factory', 'pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kabi_fusionProbe',       'rollback', '2026-05-08T16:00:00Z'),
  ('kinoko.formBlock.v1',       0, 0, 'kinoko.formBlock.v1',       1, 'py_factory', 'pymagatama.langgraph_graphs._single_task_wrapper:build_graph_kinoko_formBlock',       'rollback', '2026-05-08T16:00:00Z'),
  ('hakkou.createFerment.v1',   0, 0, 'hakkou.createFerment.v1',   1, 'py_factory', 'pymagatama.langgraph_graphs._single_task_wrapper:build_graph_hakkou_createFerment',   'rollback', '2026-05-08T16:00:00Z'),
  ('hakkou.llmTransform.v1',    0, 0, 'hakkou.llmTransform.v1',    1, 'py_factory', 'pymagatama.langgraph_graphs._single_task_wrapper:build_graph_hakkou_llmTransform',    'rollback', '2026-05-08T16:00:00Z'),
  ('hakkou.finalizeFerment.v1', 0, 0, 'hakkou.finalizeFerment.v1', 1, 'py_factory', 'pymagatama.langgraph_graphs._single_task_wrapper:build_graph_hakkou_finalizeFerment', 'rollback', '2026-05-08T16:00:00Z');
