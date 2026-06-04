-- ADR-2605082000 Phase A — coverageGap + yoro_platform_pulse canonical batch.
--
-- bulk-51 specs:
--   coverage_gap_bridge: stats_sync → scan → ingest → infer → generate → END (5 nodes)
--   yoro_platform_pulse: platform_pulse → END (1 node)
--
-- coverageGap canonical actor exposes 5 tools (all 5 used by v2). yoro
-- canonical actor exposes 8 tools (1 used by v2 — others shelf-stocked
-- per agentEconomy pattern). Worker hostnames use kebab-case
-- (coverage-gap.etzhayyim.com / yoro.etzhayyim.com).

-- coverageGap: 5 tools, all used by v2
INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:coverage-gap.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-coverageGap-statsSync',
   0, 0, 'com.etzhayyim.apps.coverageGap.statsSync', 'did:web:coverage-gap.etzhayyim.com', 'coverage-gap.etzhayyim.com', 'procedure',
   'Sync world coverage stats baseline.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/coverageGap/statsSync.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:coverage-gap.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-coverageGap-scan',
   0, 0, 'com.etzhayyim.apps.coverageGap.scan', 'did:web:coverage-gap.etzhayyim.com', 'coverage-gap.etzhayyim.com', 'procedure',
   'Scan domains for coverage gaps.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/coverageGap/scan.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:coverage-gap.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-coverageGap-ingest',
   0, 0, 'com.etzhayyim.apps.coverageGap.ingest', 'did:web:coverage-gap.etzhayyim.com', 'coverage-gap.etzhayyim.com', 'procedure',
   'Ingest data for a coverage gap domain.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/coverageGap/ingest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:coverage-gap.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-coverageGap-infer',
   0, 0, 'com.etzhayyim.apps.coverageGap.infer', 'did:web:coverage-gap.etzhayyim.com', 'coverage-gap.etzhayyim.com', 'procedure',
   'LLM-infer missing coverage rows.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/coverageGap/infer.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:coverage-gap.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-coverageGap-generate',
   0, 0, 'com.etzhayyim.apps.coverageGap.generate', 'did:web:coverage-gap.etzhayyim.com', 'coverage-gap.etzhayyim.com', 'procedure',
   'Generate / persist newly-discovered coverage rows.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/coverageGap/generate.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

-- yoro: 8 tools, only socialPlatformPulseGraphFallback used by v2 (shelf-stocking)
INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:yoro.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-yoro-socialPostGraphFallback',
   0, 0, 'com.etzhayyim.apps.yoro.socialPostGraphFallback', 'did:web:yoro.etzhayyim.com', 'yoro.etzhayyim.com', 'procedure',
   'Yoro social post (graph fallback).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/yoro/socialPostGraphFallback.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:yoro.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-yoro-socialPlatformPulseGraphFallback',
   0, 0, 'com.etzhayyim.apps.yoro.socialPlatformPulseGraphFallback', 'did:web:yoro.etzhayyim.com', 'yoro.etzhayyim.com', 'procedure',
   'Yoro platform pulse (graph fallback).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/yoro/socialPlatformPulseGraphFallback.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:yoro.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-yoro-socialRespondToMentionGraphFallback',
   0, 0, 'com.etzhayyim.apps.yoro.socialRespondToMentionGraphFallback', 'did:web:yoro.etzhayyim.com', 'yoro.etzhayyim.com', 'procedure',
   'Yoro respond to mention (graph fallback).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/yoro/socialRespondToMentionGraphFallback.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:yoro.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-yoro-socialRespondToFollowGraphFallback',
   0, 0, 'com.etzhayyim.apps.yoro.socialRespondToFollowGraphFallback', 'did:web:yoro.etzhayyim.com', 'yoro.etzhayyim.com', 'procedure',
   'Yoro respond to follow (graph fallback).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/yoro/socialRespondToFollowGraphFallback.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:yoro.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-yoro-actorQualityInspect',
   0, 0, 'com.etzhayyim.apps.yoro.actorQualityInspect', 'did:web:yoro.etzhayyim.com', 'yoro.etzhayyim.com', 'procedure',
   'Inspect yoro actor quality.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/yoro/actorQualityInspect.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:yoro.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-yoro-actorQualityVerify',
   0, 0, 'com.etzhayyim.apps.yoro.actorQualityVerify', 'did:web:yoro.etzhayyim.com', 'yoro.etzhayyim.com', 'procedure',
   'Verify yoro actor quality scores.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/yoro/actorQualityVerify.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:yoro.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-yoro-actorQualityEnrichProfile',
   0, 0, 'com.etzhayyim.apps.yoro.actorQualityEnrichProfile', 'did:web:yoro.etzhayyim.com', 'yoro.etzhayyim.com', 'procedure',
   'Enrich yoro actor profile metadata.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/yoro/actorQualityEnrichProfile.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:yoro.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-yoro-actorQualityEnsureSeedPost',
   0, 0, 'com.etzhayyim.apps.yoro.actorQualityEnsureSeedPost', 'did:web:yoro.etzhayyim.com', 'yoro.etzhayyim.com', 'procedure',
   'Ensure yoro actor has seed post.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/yoro/actorQualityEnsureSeedPost.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('coverage_gap_bridge.v2', 0, 0, 'coverage_gap_bridge.v2', 2, 'topology', NULL,
   '{"state_keys":["domain","worldTotal","llmTier","statsOut","scanOut","ingestOut","inferOut","generateOut","ok","error"],"entry":"stats_sync","edges":[{"from":"stats_sync","to":"scan"},{"from":"scan","to":"ingest"},{"from":"ingest","to":"infer"},{"from":"infer","to":"generate"},{"from":"generate","to":"END"}]}',
   'coverage gap bridge (topology v2, 5-node mcp_tool pipeline)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.coverage-gap.etzhayyim.com'),
  ('yoro_platform_pulse.v2', 0, 0, 'yoro_platform_pulse.v2', 2, 'topology', NULL,
   '{"state_keys":["pulseOut","ok","error"],"entry":"platform_pulse","edges":[{"from":"platform_pulse","to":"END"}]}',
   'yoro platform pulse (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.yoro.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('coverage_gap_bridge.v2:stats_sync', 0, 0, 'coverage_gap_bridge.v2', 'stats_sync',
   'mcp_tool', 'mcp://com.etzhayyim.apps.coverageGap.statsSync',
   '{"input_keys":[],"result_key":"statsOut","args":{"name":"com.etzhayyim.apps.coverageGap.statsSync"}}',
   '2026-05-09T00:00:00Z'),
  ('coverage_gap_bridge.v2:scan', 0, 0, 'coverage_gap_bridge.v2', 'scan',
   'mcp_tool', 'mcp://com.etzhayyim.apps.coverageGap.scan',
   '{"input_keys":[],"result_key":"scanOut","args":{"name":"com.etzhayyim.apps.coverageGap.scan"}}',
   '2026-05-09T00:00:00Z'),
  ('coverage_gap_bridge.v2:ingest', 0, 0, 'coverage_gap_bridge.v2', 'ingest',
   'mcp_tool', 'mcp://com.etzhayyim.apps.coverageGap.ingest',
   '{"input_keys":["domain","worldTotal"],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.coverageGap.ingest"}}',
   '2026-05-09T00:00:00Z'),
  ('coverage_gap_bridge.v2:infer', 0, 0, 'coverage_gap_bridge.v2', 'infer',
   'mcp_tool', 'mcp://com.etzhayyim.apps.coverageGap.infer',
   '{"input_keys":["domain","llmTier"],"result_key":"inferOut","args":{"name":"com.etzhayyim.apps.coverageGap.infer"}}',
   '2026-05-09T00:00:00Z'),
  ('coverage_gap_bridge.v2:generate', 0, 0, 'coverage_gap_bridge.v2', 'generate',
   'mcp_tool', 'mcp://com.etzhayyim.apps.coverageGap.generate',
   '{"input_keys":[],"result_key":"generateOut","args":{"name":"com.etzhayyim.apps.coverageGap.generate"}}',
   '2026-05-09T00:00:00Z'),
  ('yoro_platform_pulse.v2:platform_pulse', 0, 0, 'yoro_platform_pulse.v2', 'platform_pulse',
   'mcp_tool', 'mcp://com.etzhayyim.apps.yoro.socialPlatformPulseGraphFallback',
   '{"input_keys":[],"result_key":"pulseOut","args":{"name":"com.etzhayyim.apps.yoro.socialPlatformPulseGraphFallback"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'coverage_gap_bridge.v2'
 WHERE assistant_id = 'coverage_gap_bridge';
UPDATE vertex_langgraph_assistant SET superseded_by = 'yoro_platform_pulse.v2'
 WHERE assistant_id = 'yoro_platform_pulse';

FLUSH;
