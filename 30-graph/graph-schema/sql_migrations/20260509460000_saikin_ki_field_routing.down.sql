-- Rollback Phase D2 saikin/ki field-routing flip — restore the v2
-- topology rows with `router` (legacy py_primitive) conditional_edges.
-- The router functions still exist in pymagatama.langgraph_graphs.* so
-- the rollback target is functionally identical to the pre-D2 state.

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES (
  'saikin.cycle.v2', 2, 0, 'saikin.cycle.v2', 2, 'topology', NULL,
  '{"state_keys":["signalCount","signals","probeOut","transferOut","formColonyOut","handoffOut","lyseOut","signalId","colonyId","ok","error"],"entry":"probe","edges":[{"from":"form_colony","to":"handoff"},{"from":"handoff","to":"END"},{"from":"lyse","to":"END"}],"conditional_edges":[{"from":"probe","router":"pymagatama.langgraph_graphs.saikin_cycle:_has_signals_gate","paths":{"transfer":"transfer","no_signals":"END"}},{"from":"transfer","router":"pymagatama.langgraph_graphs.saikin_cycle:_transfer_outcome_gate","paths":{"form_colony":"form_colony","lyse":"lyse"}}]}',
  'saikin horizontal-transfer cycle (topology v2, mcp_tool nodes)',
  '2026-05-09T00:00:00Z'
);

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES (
  'ki.cycle.v2', 2, 0, 'ki.cycle.v2', 2, 'topology', NULL,
  '{"state_keys":["sourceVertexId","inputKind","contentSnippet","absorbOut","synthOut","artifactId","confidence","bloomOut","bloomSkipped","bloomId","ringOut","period","ok","error"],"entry":"absorb","edges":[{"from":"absorb","to":"synthesize"},{"from":"bloom","to":"ring"},{"from":"skip_bloom","to":"ring"},{"from":"ring","to":"END"}],"conditional_edges":[{"from":"synthesize","router":"pymagatama.langgraph_graphs.ki_cycle:_confidence_gate","paths":{"bloom":"bloom","skip_bloom":"skip_bloom"}}]}',
  'ki vertical-synthesis cycle (topology v2, mcp_tool nodes)',
  '2026-05-09T00:00:00Z'
);

FLUSH;
