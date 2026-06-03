-- P10.2b of ADR-2605141200 — register the aggregateCritique aggregator.
-- Follow-on to the P10.2 row in 20260514150000_seed_mangaka_validate_camera_plan_mcp_tool.up.sql.
--
-- The aggregator reads `renders[]` (with optional `critique.axes` from an
-- upstream vision LLM) + `targetMood` + `fallbackScore`, fetches each
-- render's PNG from B2 to overlay the Hume `emotionAlignment` axis, then
-- writes back `{renders, selected, score}` for the conditional refinement
-- edge to dispatch on. Hume is the data-driven authority for the
-- emotionAlignment axis (ADR-2605131115); the LLM's self-report on that
-- axis is treated as a hint.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:mangaka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-mangaka-tools-aggregateCritique',
   0, 0,
   'com.etzhayyim.apps.mangaka.tools.aggregateCritique',
   'did:web:mangaka.etzhayyim.com', 'mangaka.etzhayyim.com', 'procedure',
   'P10.2b critique aggregator: Hume emotionAlignment overlay + mean axes aggregate + best-of-N selection.',
   '{"type":"object","required":["renders"],"properties":{"renders":{"type":"array"},"targetMood":{"type":"string"},"fallbackScore":{"type":"number"}}}',
   '{"type":"object","required":["renders","selected","score"],"properties":{"renders":{"type":"array"},"selected":{"type":"object"},"score":{"type":"number"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/mangaka/tools/aggregateCritique.json',
   'anon', 'anon', '', '2026-05-14T16:00:00Z');

FLUSH;
