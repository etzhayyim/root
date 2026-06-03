-- ADR-2605141200 (mangaka 3D scene Pregel) + ADR-2605080600 (Granian L3)
-- + ADR-2605082000 (Graph-as-Data) — register the `compose_scene_3d`
-- LangGraph assistant in the RW-resident SSoT (vertex_langgraph_assistant /
-- _node / _deployment) so the bpmn-dispatcher /runs router can resolve
-- `com.etzhayyim.apps.mangaka.composeScene3d` → assistant version → compiled graph.
--
-- Phase A (this migration, active): kind='py_factory' pointing at
--   `lg_mangaka.graphs.compose_scene_3d:build_graph`. Uses the existing
--   in-tree Python graph — no node decomposition required.
-- Phase B (compose_scene_3d.topology.yaml, scaffolded): kind='topology' row
--   pending the 6 MCP tools listed there. When ready, a follow-up migration
--   inserts (v2, kind='topology', spec=<yaml→json>) + flips the deployment
--   to v2 status='active' and the v1 py_factory row to inactive.
--
-- Idempotent — NOT EXISTS guards mirror the pattern in
-- 20260510100000_seed_site_common_crawl_langgraph.up.sql.

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   description, checkpointer_mode, authored_by, created_at)
SELECT
  'com.etzhayyim.apps.mangaka.composeScene3d', 0, 0,
  'com.etzhayyim.apps.mangaka.composeScene3d', 1, 'py_factory',
  'lg_mangaka.graphs.compose_scene_3d:build_graph',
  'mangaka compose_scene_3d — 9 super-step Pregel (P0–P5 of ADR-2605141200)',
  'postgres',
  'did:web:mangaka.etzhayyim.com',
  '2026-05-14T13:00:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_assistant
  WHERE assistant_id = 'com.etzhayyim.apps.mangaka.composeScene3d'
    AND version = 1
);

INSERT INTO vertex_langgraph_deployment
  (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status,
   replicas, updated_at)
SELECT
  'com.etzhayyim.apps.mangaka.composeScene3d', 0, 0,
  'com.etzhayyim.apps.mangaka.composeScene3d',
  'com.etzhayyim.apps.mangaka.composeScene3d', 1, 'active', 1,
  '2026-05-14T13:00:00Z'
WHERE NOT EXISTS (
  SELECT 1 FROM vertex_langgraph_deployment
  WHERE nsid = 'com.etzhayyim.apps.mangaka.composeScene3d'
);
