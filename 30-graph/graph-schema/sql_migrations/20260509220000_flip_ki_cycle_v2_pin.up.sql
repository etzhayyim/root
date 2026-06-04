-- ADR-2605082000 PoC go-live (ki) — flip the ki.cycle deployment pin v1 → v2.
--
-- Pre-conditions (operator must verify before applying):
--   1. r_20260509190000_seed_ki_mcp_tools applied — vertex_mcp_tool_def has
--      4 enabled rows for com.etzhayyim.apps.ki.* (actor_host=ki.etzhayyim.com).
--   2. r_20260509200000_topology_ki_cycle_v2_mcp applied — assistant
--      ki.cycle.v2 + 5 mcp_tool node rows exist (4 actor + 1 const.echo).
--   3. r_20260509210000_seed_tools_const_mcp applied — vertex_mcp_tool_def
--      has the com.etzhayyim.tools.const.echo row (skip_bloom dependency).
--   4. dispatcher (pymagatama/dispatcher_main.py) is deployed with the
--      `/xrpc/com.etzhayyim.mcp.message` route AND _DEFAULT_ACTORS includes
--      ("ki", [...]) AND _build_const_overrides registers tools.const.echo.
--   5. ki.etzhayyim.com Worker (`60-apps/etzhayyim-project-ki/src/app.ts`) is
--      deployed with the MCP_NSID branch in fetch().
--   6. End-to-end smoke test passed:
--        curl -X POST https://ki.etzhayyim.com/xrpc/com.etzhayyim.mcp.message \
--          -H 'Content-Type: application/json' \
--          -d '{"method":"tools/call","params":{"name":"com.etzhayyim.apps.ki.absorb","arguments":{"sourceVertexId":"at://test/x"}}}'
--        curl -X POST https://ki.etzhayyim.com/xrpc/com.etzhayyim.mcp.message \
--          -H 'Content-Type: application/json' \
--          -d '{"method":"tools/call","params":{"name":"com.etzhayyim.tools.const.echo","arguments":{"constant":{"k":1}}}}'
--      Both → 200 OK with `{"result":{...}}`.

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at)
VALUES
  ('langgraph.builtin.ki.cycle.v1', 0, 0,
   'langgraph.builtin.ki.cycle.v1', 'ki.cycle.v2', 2, 'active', 1,
   '2026-05-09T00:00:00Z');

FLUSH;
