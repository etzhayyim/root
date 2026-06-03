-- ADR-2605082000 Phase A — aria canonical-actor consolidation.
--
-- bulk-51 has 7 aria_* assistants (1 node each, all py_primitive). This
-- migration:
--   1. Seeds vertex_mcp_tool_def with 8 com.etzhayyim.apps.aria.* rows
--      (matches mcp_dispatch._DEFAULT_ACTORS aria entry: 8 methods, including
--      `reverseTopoReplan` which has no bulk-51 assistant but is ready in
--      pymagatama.primitives.aria_signal:task_aria_reverse_topo_replan).
--   2. Inserts 7 aria_*.v2 assistants (one per existing bulk-51 row) with
--      kind=topology, single mcp_tool node bound via the canonical NSID.
--   3. Marks each bulk-51 v1 as superseded by its corresponding v2.
--
-- Schema fields use stub schemas (`{"type":"object"}`) — same approach as
-- the adsk PoC. Lexicon authoring is a follow-up iter.
--
-- RUNTIME CAVEAT: aria.etzhayyim.com Worker does NOT exist yet. The MCP envelope
-- POST to https://aria.etzhayyim.com/xrpc/com.etzhayyim.mcp.message will fail at edge
-- until either (a) Worker is created (saikin/ki template), or
-- (b) UPDATE vertex_mcp_tool_def SET actor_host='saikin.etzhayyim.com'
--     WHERE nsid LIKE 'com.etzhayyim.apps.aria.%'  to route via existing proxy.
--
-- This is the FIRST canonical-actor data-layer migration (iter27).
-- saikin/ki/adsk migrations were per-assistant; aria proves the pattern
-- generalises to multi-assistant clusters.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:aria.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-aria-attentionIngest',
   0, 0, 'com.etzhayyim.apps.aria.attentionIngest', 'did:web:aria.etzhayyim.com', 'aria.etzhayyim.com', 'procedure',
   'aria attention signal ingest (cross-platform attention metrics).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/aria/attentionIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:aria.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-aria-emotionIngest',
   0, 0, 'com.etzhayyim.apps.aria.emotionIngest', 'did:web:aria.etzhayyim.com', 'aria.etzhayyim.com', 'procedure',
   'aria emotion signal ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/aria/emotionIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:aria.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-aria-influenceIngest',
   0, 0, 'com.etzhayyim.apps.aria.influenceIngest', 'did:web:aria.etzhayyim.com', 'aria.etzhayyim.com', 'procedure',
   'aria influence signal ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/aria/influenceIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:aria.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-aria-marketDeltaIngest',
   0, 0, 'com.etzhayyim.apps.aria.marketDeltaIngest', 'did:web:aria.etzhayyim.com', 'aria.etzhayyim.com', 'procedure',
   'aria market-delta signal ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/aria/marketDeltaIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:aria.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-aria-minimaxSweep',
   0, 0, 'com.etzhayyim.apps.aria.minimaxSweep', 'did:web:aria.etzhayyim.com', 'aria.etzhayyim.com', 'procedure',
   'aria minimax sweep over signal sources.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/aria/minimaxSweep.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:aria.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-aria-moneyFlowIngest',
   0, 0, 'com.etzhayyim.apps.aria.moneyFlowIngest', 'did:web:aria.etzhayyim.com', 'aria.etzhayyim.com', 'procedure',
   'aria money-flow signal ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/aria/moneyFlowIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:aria.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-aria-requestIngest',
   0, 0, 'com.etzhayyim.apps.aria.requestIngest', 'did:web:aria.etzhayyim.com', 'aria.etzhayyim.com', 'procedure',
   'aria request-pulse signal ingest.',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/aria/requestIngest.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:aria.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-aria-reverseTopoReplan',
   0, 0, 'com.etzhayyim.apps.aria.reverseTopoReplan', 'did:web:aria.etzhayyim.com', 'aria.etzhayyim.com', 'procedure',
   'aria reverse-topology replan (no bulk-51 assistant; primitive ready).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/aria/reverseTopoReplan.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

-- 7 v2 assistants — one per bulk-51 sibling. Each has a single mcp_tool node.

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('aria_attention_ingest.v2', 0, 0, 'aria_attention_ingest.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"attention_ingest","edges":[{"from":"attention_ingest","to":"END"}]}',
   'aria attention ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.aria.etzhayyim.com'),
  ('aria_emotion_ingest.v2', 0, 0, 'aria_emotion_ingest.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"emotion_ingest","edges":[{"from":"emotion_ingest","to":"END"}]}',
   'aria emotion ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.aria.etzhayyim.com'),
  ('aria_influence_ingest.v2', 0, 0, 'aria_influence_ingest.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"influence_ingest","edges":[{"from":"influence_ingest","to":"END"}]}',
   'aria influence ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.aria.etzhayyim.com'),
  ('aria_market_ingest.v2', 0, 0, 'aria_market_ingest.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"market_delta_ingest","edges":[{"from":"market_delta_ingest","to":"END"}]}',
   'aria market-delta ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.aria.etzhayyim.com'),
  ('aria_minimax_sweep.v2', 0, 0, 'aria_minimax_sweep.v2', 2, 'topology', NULL,
   '{"state_keys":["sweepOut","ok","error"],"entry":"minimax_sweep","edges":[{"from":"minimax_sweep","to":"END"}]}',
   'aria minimax sweep (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.aria.etzhayyim.com'),
  ('aria_money_flow_ingest.v2', 0, 0, 'aria_money_flow_ingest.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"money_flow_ingest","edges":[{"from":"money_flow_ingest","to":"END"}]}',
   'aria money-flow ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.aria.etzhayyim.com'),
  ('aria_request_ingest.v2', 0, 0, 'aria_request_ingest.v2', 2, 'topology', NULL,
   '{"state_keys":["ingestOut","ok","error"],"entry":"request_ingest","edges":[{"from":"request_ingest","to":"END"}]}',
   'aria request ingest (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.aria.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('aria_attention_ingest.v2:attention_ingest', 0, 0, 'aria_attention_ingest.v2', 'attention_ingest',
   'mcp_tool', 'mcp://com.etzhayyim.apps.aria.attentionIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.aria.attentionIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('aria_emotion_ingest.v2:emotion_ingest', 0, 0, 'aria_emotion_ingest.v2', 'emotion_ingest',
   'mcp_tool', 'mcp://com.etzhayyim.apps.aria.emotionIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.aria.emotionIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('aria_influence_ingest.v2:influence_ingest', 0, 0, 'aria_influence_ingest.v2', 'influence_ingest',
   'mcp_tool', 'mcp://com.etzhayyim.apps.aria.influenceIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.aria.influenceIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('aria_market_ingest.v2:market_delta_ingest', 0, 0, 'aria_market_ingest.v2', 'market_delta_ingest',
   'mcp_tool', 'mcp://com.etzhayyim.apps.aria.marketDeltaIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.aria.marketDeltaIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('aria_minimax_sweep.v2:minimax_sweep', 0, 0, 'aria_minimax_sweep.v2', 'minimax_sweep',
   'mcp_tool', 'mcp://com.etzhayyim.apps.aria.minimaxSweep',
   '{"input_keys":[],"result_key":"sweepOut","args":{"name":"com.etzhayyim.apps.aria.minimaxSweep"}}',
   '2026-05-09T00:00:00Z'),
  ('aria_money_flow_ingest.v2:money_flow_ingest', 0, 0, 'aria_money_flow_ingest.v2', 'money_flow_ingest',
   'mcp_tool', 'mcp://com.etzhayyim.apps.aria.moneyFlowIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.aria.moneyFlowIngest"}}',
   '2026-05-09T00:00:00Z'),
  ('aria_request_ingest.v2:request_ingest', 0, 0, 'aria_request_ingest.v2', 'request_ingest',
   'mcp_tool', 'mcp://com.etzhayyim.apps.aria.requestIngest',
   '{"input_keys":[],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.aria.requestIngest"}}',
   '2026-05-09T00:00:00Z');

-- Mark v1s as superseded.
UPDATE vertex_langgraph_assistant SET superseded_by = 'aria_attention_ingest.v2' WHERE assistant_id = 'aria_attention_ingest';
UPDATE vertex_langgraph_assistant SET superseded_by = 'aria_emotion_ingest.v2'   WHERE assistant_id = 'aria_emotion_ingest';
UPDATE vertex_langgraph_assistant SET superseded_by = 'aria_influence_ingest.v2' WHERE assistant_id = 'aria_influence_ingest';
UPDATE vertex_langgraph_assistant SET superseded_by = 'aria_market_ingest.v2'    WHERE assistant_id = 'aria_market_ingest';
UPDATE vertex_langgraph_assistant SET superseded_by = 'aria_minimax_sweep.v2'    WHERE assistant_id = 'aria_minimax_sweep';
UPDATE vertex_langgraph_assistant SET superseded_by = 'aria_money_flow_ingest.v2' WHERE assistant_id = 'aria_money_flow_ingest';
UPDATE vertex_langgraph_assistant SET superseded_by = 'aria_request_ingest.v2'   WHERE assistant_id = 'aria_request_ingest';

FLUSH;
