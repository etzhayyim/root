-- P10.2 of ADR-2605141200 — register the validateCameraPlan validator MCP
-- tool. Follow-on to 20260514140000_seed_mangaka_compose_scene_3d_mcp_tools
-- which seeded the 6 core tools; this row plugs the validator between the
-- cinematography LLM node and the simulate_one fan-out (Phase B blocker #2).
--
-- Once seeded, `_resolve_mcp_nsid` resolves
-- `mcp://com.etzhayyim.apps.mangaka.tools.validateCameraPlan` to
-- `mangaka.etzhayyim.com`. The `/xrpc/{nsid}` dispatcher (server.py P9)
-- forwards to `lg_mangaka.tools.tool_validate_camera_plan`. PK=vertex_id,
-- so re-INSERT is RW implicit upsert.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-validateCameraPlan',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.validateCameraPlan',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P10.2 validator: clamp shot/fov/roll/dof + canonicalise lights between cinematography LLM and simulate_one.',
   '{"type":"object","required":["cameraPlanRaw"],"properties":{"cameraPlanRaw":{"type":"object"},"fallbackShot":{"type":"string"}}}',
   '{"type":"object","required":["cameraPlan"],"properties":{"cameraPlan":{"type":"object","required":["camera","lights"],"properties":{"camera":{"type":"object"},"lights":{"type":"array"},"llm":{"type":"boolean"}}}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/validateCameraPlan.json',
   'anon', 'anon', '', '2026-05-14T15:00:00Z');

FLUSH;
