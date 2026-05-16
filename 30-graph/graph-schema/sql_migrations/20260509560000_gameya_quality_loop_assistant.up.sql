-- Register gameya_quality_loop as an RW-resident LangGraph assistant.
--
-- The Python module remains the source of executable graph code; these rows
-- make the deployment discoverable by langgraph_loader/langgraph_watcher
-- instead of relying only on the static fallback registry.

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, owner_did, assistant_id, version, kind,
   factory_path, spec, description, created_at, checkpointer_mode)
VALUES
  ('gameya_quality_loop', 0, 0, 'did:web:gameya.gftd.ai',
   'gameya_quality_loop', 1, 'py_factory',
   'pymagatama.langgraph_graphs.gameya_quality_loop:build_graph',
   NULL,
   'gameya.gftd.ai deterministic playtest quality loop: observe, score, propose, package release gate.',
   '2026-05-09T09:56:00Z', 'rw_vertex');

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, owner_did, nsid, assistant_id, version,
   status, replicas, updated_at)
VALUES
  ('langgraph.builtin.gameya_quality_loop', 0, 0, 'did:web:gameya.gftd.ai',
   'langgraph.builtin.gameya_quality_loop', 'gameya_quality_loop', 1,
   'active', 1, '2026-05-09T09:56:00Z');

FLUSH;
