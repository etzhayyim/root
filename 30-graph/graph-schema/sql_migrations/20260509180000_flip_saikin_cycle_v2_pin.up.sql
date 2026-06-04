-- ADR-2605082000 PoC go-live — flip the saikin.cycle deployment pin from v1 → v2.
--
-- Pre-conditions (operator must verify before applying):
--   1. r_20260509160000_seed_saikin_mcp_tools applied — vertex_mcp_tool_def
--      has 5 enabled rows for com.etzhayyim.apps.saikin.* with actor_host=saikin.etzhayyim.com.
--      Verify:
--        SELECT nsid, actor_host, enabled FROM vertex_mcp_tool_def
--         WHERE nsid LIKE 'com.etzhayyim.apps.saikin.%';
--   2. r_20260509170000_topology_saikin_cycle_v2_mcp applied — assistant
--      saikin.cycle.v2 + 5 mcp_tool node rows exist.
--      Verify:
--        SELECT version, kind, checkpointer_mode FROM vertex_langgraph_assistant
--         WHERE assistant_id = 'saikin.cycle.v2';
--   3. dispatcher (pymagatama/dispatcher_main.py) is deployed with the
--      `/xrpc/com.etzhayyim.mcp.message` route registered (commit that touches
--      `pymagatama/mcp_dispatch.py` is live).
--   4. saikin.etzhayyim.com Worker (`60-apps/etzhayyim-project-saikin/src/app.ts`) is
--      deployed with the MCP_NSID branch in fetch().
--   5. End-to-end smoke test passed:
--        curl -X POST https://saikin.etzhayyim.com/xrpc/com.etzhayyim.mcp.message \
--          -H 'Content-Type: application/json' \
--          -d '{"method":"tools/call","params":{"name":"com.etzhayyim.apps.saikin.probeEnvironment","arguments":{}}}'
--      → 200 OK with `{"result":{"signalCount":...,"signals":[...]}}`.
--
-- Rollback: re-INSERT the v1 pin row (vertex_id PK = nsid, RW implicit upsert).

-- Flip the active pin: same nsid PK, point at saikin.cycle.v2 instead of v1.
INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at)
VALUES
  ('langgraph.builtin.saikin.cycle.v1', 0, 0,
   'langgraph.builtin.saikin.cycle.v1', 'saikin.cycle.v2', 2, 'active', 1,
   '2026-05-09T00:00:00Z');

FLUSH;
