-- ADR-2605082000 Phase D2 — flip saikin/ki v2 conditional_edges from
-- legacy py_primitive `router` to data-driven `field` routing.
--
-- Source code-island retired:
--   pymagatama.langgraph_graphs.saikin_cycle:_has_signals_gate
--   pymagatama.langgraph_graphs.saikin_cycle:_transfer_outcome_gate
--   pymagatama.langgraph_graphs.ki_cycle:_confidence_gate
--
-- The route decision is now embedded in the upstream MCP primitive's
-- response (`nextRoute` field, set by saikin_worker_main.task_probe_environment
-- / task_transfer_signal / ki_worker_main.task_synthesize). The conditional
-- edge reads `<resultKey>.result.nextRoute` via the same dotted-path
-- navigator used by tools.json.extract.
--
-- Same-PK INSERT semantics: RisingWave overwrites the existing topology
-- row. The audit script's two-pass `latestKind` / `fileOrder` resolution
-- ensures only this re-INSERT counts as live. assistant_id stays the
-- same (no superseded_by needed) — this is a config-only swap.

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES (
  'saikin.cycle.v2', 3, 0, 'saikin.cycle.v2', 3, 'topology', NULL,
  '{"state_keys":["signalCount","signals","probeOut","transferOut","formColonyOut","handoffOut","lyseOut","signalId","colonyId","ok","error"],"entry":"probe","edges":[{"from":"form_colony","to":"handoff"},{"from":"handoff","to":"END"},{"from":"lyse","to":"END"}],"conditional_edges":[{"from":"probe","field":"probeOut.result.nextRoute","paths":{"transfer":"transfer","no_signals":"END"},"default":"no_signals"},{"from":"transfer","field":"transferOut.result.nextRoute","paths":{"form_colony":"form_colony","lyse":"lyse"},"default":"lyse"}]}',
  'saikin horizontal-transfer cycle (topology v2, mcp_tool nodes, field-based routing per ADR-2605082000 Phase D2)',
  '2026-05-09T05:00:00Z'
);

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES (
  'ki.cycle.v2', 3, 0, 'ki.cycle.v2', 3, 'topology', NULL,
  '{"state_keys":["sourceVertexId","inputKind","contentSnippet","absorbOut","synthOut","artifactId","confidence","bloomOut","bloomSkipped","bloomId","ringOut","period","ok","error"],"entry":"absorb","edges":[{"from":"absorb","to":"synthesize"},{"from":"bloom","to":"ring"},{"from":"skip_bloom","to":"ring"},{"from":"ring","to":"END"}],"conditional_edges":[{"from":"synthesize","field":"synthOut.result.nextRoute","paths":{"bloom":"bloom","skip_bloom":"skip_bloom"},"default":"skip_bloom"}]}',
  'ki vertical-synthesis cycle (topology v2, mcp_tool nodes, field-based routing per ADR-2605082000 Phase D2)',
  '2026-05-09T05:00:00Z'
);

FLUSH;
