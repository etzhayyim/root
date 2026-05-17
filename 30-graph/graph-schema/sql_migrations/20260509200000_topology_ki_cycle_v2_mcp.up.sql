-- ADR-2605082000 PoC — ki.cycle.v2 with kind=mcp_tool nodes (sibling of saikin v2).
--
-- All 5 nodes are now data-resolved: 4 actor tools + 1 generic
-- `ai.gftd.tools.const.echo` for the identity `skip_bloom` step.
-- Zero py_primitive rows in this migration.

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord,
   assistant_id, version, kind, factory_path, spec, description, created_at,
   checkpointer_mode, authored_by)
VALUES (
  'ki.cycle.v2', 0, 0,
  'ki.cycle.v2', 2, 'topology', NULL,
  '{"state_keys":["sourceVertexId","inputKind","contentSnippet","absorbOut","synthOut","artifactId","confidence","bloomOut","bloomSkipped","bloomId","ringOut","period","ok","error"],"entry":"absorb","edges":[{"from":"absorb","to":"synthesize"},{"from":"bloom","to":"ring"},{"from":"skip_bloom","to":"ring"},{"from":"ring","to":"END"}],"conditional_edges":[{"from":"synthesize","router":"pymagatama.langgraph_graphs.ki_cycle:_confidence_gate","paths":{"bloom":"bloom","skip_bloom":"skip_bloom"}}]}',
  'ki vertical-synthesis cycle (topology v2, mcp_tool nodes)',
  '2026-05-09T00:00:00Z',
  'rw_vertex',
  'did:web:agent.ki.etzhayyim.com'
);

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('ki.cycle.v2:absorb',     0, 0, 'ki.cycle.v2', 'absorb',
   'mcp_tool', 'mcp://ai.gftd.apps.ki.absorb',
   '{"input_keys":["sourceVertexId","inputKind","contentSnippet"],"result_key":"absorbOut","args":{"name":"ai.gftd.apps.ki.absorb"}}',
   '2026-05-09T00:00:00Z'),
  ('ki.cycle.v2:synthesize', 0, 0, 'ki.cycle.v2', 'synthesize',
   'mcp_tool', 'mcp://ai.gftd.apps.ki.synthesize',
   '{"input_keys":["absorbId"],"result_key":"synthOut","args":{"name":"ai.gftd.apps.ki.synthesize"}}',
   '2026-05-09T00:00:00Z'),
  ('ki.cycle.v2:bloom',      0, 0, 'ki.cycle.v2', 'bloom',
   'mcp_tool', 'mcp://ai.gftd.apps.ki.bloom',
   '{"input_keys":["artifactId"],"result_key":"bloomOut","args":{"name":"ai.gftd.apps.ki.bloom"}}',
   '2026-05-09T00:00:00Z'),
  ('ki.cycle.v2:ring',       0, 0, 'ki.cycle.v2', 'ring',
   'mcp_tool', 'mcp://ai.gftd.apps.ki.ring',
   '{"input_keys":["period"],"result_key":"ringOut","args":{"name":"ai.gftd.apps.ki.ring"}}',
   '2026-05-09T00:00:00Z'),
  -- skip_bloom: identity node returning a constant. Bound via the generic
  -- ai.gftd.tools.const.echo primitive (config.args.constant carries the
  -- payload directly; state is ignored).
  ('ki.cycle.v2:skip_bloom', 0, 0, 'ki.cycle.v2', 'skip_bloom',
   'mcp_tool', 'mcp://ai.gftd.tools.const.echo',
   '{"input_keys":[],"result_key":"bloomOut","args":{"name":"ai.gftd.tools.const.echo","constant":{"bloomSkipped":true,"bloomId":null}}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant
   SET superseded_by = 'ki.cycle.v2'
 WHERE assistant_id = 'ki.cycle.v1';

-- DO NOT flip deployment pin yet — same operator gate as saikin
-- (see r_20260509180000_flip_saikin_cycle_v2_pin.up.sql).

FLUSH;
