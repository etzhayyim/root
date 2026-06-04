-- P8 of ADR-2605141200 — register the 6 compose_scene_3d MCP tools in
-- vertex_mcp_tool_def. Mirrors the saikin seed pattern
-- (20260509160000_seed_saikin_mcp_tools.up.sql).
--
-- Phase C activation depends on these rows: once present,
-- `_resolve_mcp_nsid` in pymagatama/langgraph_node_resolvers.py can answer
-- `SELECT actor_host FROM vertex_mcp_tool_def WHERE nsid = 'com.etzhayyim.apps.mangaka.tools.<m>'`,
-- and a topology assistant node bound as kind=mcp_tool ref=mcp://...
-- resolves to https://mangaka.etzhayyim.com/xrpc/com.etzhayyim.mcp.message at runtime.
--
-- vertex_id slug = NSID with dots replaced by `-` (sync-mcp-registry.py
-- convention). Schemas below are compact JSON-Schema (Draft 2020-12) —
-- sync-mcp-registry.py will reconcile schema_hash + version on the next
-- `etzhayyim contract sync` run; PK=vertex_id makes the upsert idempotent.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  -- 1. loadPanelPlan
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-loadPanelPlan',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.loadPanelPlan',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'Pregel step 1: read kind=panel from vertex_mangaka, emit normalised panel_plan.',
   '{"type":"object","required":["panelRkey"],"properties":{"panelRkey":{"type":"string"},"rwUrl":{"type":"string"}}}',
   '{"type":"object","properties":{"panelPlan":{"type":"object"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/loadPanelPlan.json',
   'anon', 'anon', '', '2026-05-14T14:00:00Z'),

  -- 2. resolveAssets
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-resolveAssets',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.resolveAssets',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'Pregel step 2: resolve character / environment / prop vertices to VRM/glTF blob_keys.',
   '{"type":"object","required":["panelPlan"],"properties":{"panelPlan":{"type":"object"},"rwUrl":{"type":"string"}}}',
   '{"type":"object","properties":{"assetRefs":{"type":"object"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/resolveAssets.json',
   'anon', 'anon', '', '2026-05-14T14:00:00Z'),

  -- 3. placeScene
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-placeScene',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.placeScene',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'Pregel step 4: compose scene_dag JSON-LD from panel_plan + asset_refs + pose_plan. Pure CPU.',
   '{"type":"object","required":["panelPlan","assetRefs","posePlan"],"properties":{"panelPlan":{"type":"object"},"assetRefs":{"type":"object"},"posePlan":{"type":"object"}}}',
   '{"type":"object","properties":{"sceneDag":{"type":"object"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/placeScene.json',
   'anon', 'anon', '', '2026-05-14T14:00:00Z'),

  -- 4. simulateCharacter (per-character Send fan-out)
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-simulateCharacter',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.simulateCharacter',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'Pregel step 6 (per character via Send): spring-bone + cloth settle.',
   '{"type":"object","required":["charRkey"],"properties":{"charRkey":{"type":"string"},"pose":{"type":"object"},"ticks":{"type":"integer","minimum":1,"maximum":240}}}',
   '{"type":"object","properties":{"simResult":{"type":"object"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/simulateCharacter.json',
   'anon', 'anon', '', '2026-05-14T14:00:00Z'),

  -- 5. renderKeyframes (GPU-bound — pod selector vke-render-pool)
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-renderKeyframes',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.renderKeyframes',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'Pregel step 7: headless wgpu render via kami-mangaka-scene PyO3 wheel + B2 content-addressed PUT. Pod selector vke-render-pool.',
   '{"type":"object","required":["cameraPlan","sceneDag","panelRkey","iteration"],"properties":{"cameraPlan":{"type":"object"},"sceneDag":{"type":"object"},"panelRkey":{"type":"string"},"iteration":{"type":"integer","minimum":0},"renderAngles":{"type":"integer","minimum":1,"maximum":5},"simSeed":{"type":"integer"}}}',
   '{"type":"object","required":["renders","iteration"],"properties":{"renders":{"type":"array","items":{"type":"object","properties":{"blobKey":{"type":"string"},"depthBlobKey":{"type":"string"},"outlineBlobKey":{"type":"string"},"score":{"type":"number"},"angle":{"type":"string"}},"required":["blobKey"]}},"iteration":{"type":"integer"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/renderKeyframes.json',
   'anon', 'anon', '', '2026-05-14T14:00:00Z'),

  -- 6. persistScene3d (terminal — INSERT vertex_mangaka_scene_3d on pod, ADR-2605111200)
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-persistScene3d',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.persistScene3d',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'Pregel step 9: INSERT into vertex_mangaka_scene_3d (asyncpg on pod, never on CF Worker).',
   '{"type":"object","required":["panelRkey","iteration","selected","sceneDag","cameraPlan","posePlan","score","simSeed"],"properties":{"panelRkey":{"type":"string"},"iteration":{"type":"integer","minimum":0},"selected":{"type":"object"},"sceneDag":{"type":"object"},"cameraPlan":{"type":"object"},"posePlan":{"type":"object"},"score":{"type":"number"},"simSeed":{"type":"integer"},"dryRun":{"type":"boolean"},"rwUrl":{"type":"string"}}}',
   '{"type":"object","properties":{"sceneRkey":{"type":"string"},"status":{"type":"string"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/persistScene3d.json',
   'anon', 'anon', '', '2026-05-14T14:00:00Z');

FLUSH;
