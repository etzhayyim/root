-- Convert 8 organism single-task wrapper rows from kind=py_factory (pointing at
-- _single_task_wrapper:build_graph_<name> shim) to kind=single_task (factory_path
-- = direct task ref). Loader/watcher build the SingleTaskState graph internally.
-- _single_task_wrapper.py remains in image for the build_single_task_graph helper.

INSERT INTO vertex_langgraph_assistant (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at) VALUES
  ('kobo.budAgent.v1',          0, 0, 'kobo.budAgent.v1',          1, 'single_task', 'pymagatama.kobo_worker_main:task_bud_agent',           NULL, 'P3 single_task', '2026-05-08T19:30:00Z'),
  ('kobo.sporulate.v1',         0, 0, 'kobo.sporulate.v1',         1, 'single_task', 'pymagatama.kobo_worker_main:task_sporulate',           NULL, 'P3 single_task', '2026-05-08T19:30:00Z'),
  ('kobo.germinate.v1',         0, 0, 'kobo.germinate.v1',         1, 'single_task', 'pymagatama.kobo_worker_main:task_germinate',           NULL, 'P3 single_task', '2026-05-08T19:30:00Z'),
  ('kabi.fusionProbe.v1',       0, 0, 'kabi.fusionProbe.v1',       1, 'single_task', 'pymagatama.kabi_worker_main:task_anastomosis_probe',   NULL, 'P3 single_task', '2026-05-08T19:30:00Z'),
  ('kinoko.formBlock.v1',       0, 0, 'kinoko.formBlock.v1',       1, 'single_task', 'pymagatama.kinoko_worker_main:task_check_flow_threshold', NULL, 'P3 single_task', '2026-05-08T19:30:00Z'),
  ('hakkou.createFerment.v1',   0, 0, 'hakkou.createFerment.v1',   1, 'single_task', 'pymagatama.hakkou_worker_main:task_create_ferment_record', NULL, 'P3 single_task', '2026-05-08T19:30:00Z'),
  ('hakkou.llmTransform.v1',    0, 0, 'hakkou.llmTransform.v1',    1, 'single_task', 'pymagatama.hakkou_worker_main:task_llm_transform',     NULL, 'P3 single_task', '2026-05-08T19:30:00Z'),
  ('hakkou.finalizeFerment.v1', 0, 0, 'hakkou.finalizeFerment.v1', 1, 'single_task', 'pymagatama.hakkou_worker_main:task_finalize_ferment',  NULL, 'P3 single_task', '2026-05-08T19:30:00Z');

-- Bump deployment updated_at so watcher reloads each.
INSERT INTO vertex_langgraph_deployment (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at) VALUES
  ('langgraph.builtin.kobo.budAgent.v1',          0, 0, 'langgraph.builtin.kobo.budAgent.v1',          'kobo.budAgent.v1',          1, 'active', 1, '2026-05-08T19:30:00Z'),
  ('langgraph.builtin.kobo.sporulate.v1',         0, 0, 'langgraph.builtin.kobo.sporulate.v1',         'kobo.sporulate.v1',         1, 'active', 1, '2026-05-08T19:30:00Z'),
  ('langgraph.builtin.kobo.germinate.v1',         0, 0, 'langgraph.builtin.kobo.germinate.v1',         'kobo.germinate.v1',         1, 'active', 1, '2026-05-08T19:30:00Z'),
  ('langgraph.builtin.kabi.fusionProbe.v1',       0, 0, 'langgraph.builtin.kabi.fusionProbe.v1',       'kabi.fusionProbe.v1',       1, 'active', 1, '2026-05-08T19:30:00Z'),
  ('langgraph.builtin.kinoko.formBlock.v1',       0, 0, 'langgraph.builtin.kinoko.formBlock.v1',       'kinoko.formBlock.v1',       1, 'active', 1, '2026-05-08T19:30:00Z'),
  ('langgraph.builtin.hakkou.createFerment.v1',   0, 0, 'langgraph.builtin.hakkou.createFerment.v1',   'hakkou.createFerment.v1',   1, 'active', 1, '2026-05-08T19:30:00Z'),
  ('langgraph.builtin.hakkou.llmTransform.v1',    0, 0, 'langgraph.builtin.hakkou.llmTransform.v1',    'hakkou.llmTransform.v1',    1, 'active', 1, '2026-05-08T19:30:00Z'),
  ('langgraph.builtin.hakkou.finalizeFerment.v1', 0, 0, 'langgraph.builtin.hakkou.finalizeFerment.v1', 'hakkou.finalizeFerment.v1', 1, 'active', 1, '2026-05-08T19:30:00Z');
