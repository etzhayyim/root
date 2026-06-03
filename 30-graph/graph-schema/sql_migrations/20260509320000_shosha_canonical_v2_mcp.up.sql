-- ADR-2605082000 Phase A — shosha cluster (6 of 7 assistants).
--
-- Uses com.etzhayyim.tools.audit.emit (r_20260509310000) to fully data-resolve
-- emit_audit nodes that were py_primitive in bulk-51.
--
-- Excluded: shosha_agent_loop (fetchContext + callLlm are self_logic per
-- iter25 NO_TASK_IMPORT spot-check). It will migrate after those nodes
-- get refactored into pymagatama.primitives.shosha primitives.
--
-- Bulk-51 graph topologies (preserved):
--   daily_report:           compose_report → emit_audit → END
--   market_intelligence:    ingest_prices → ingest_freight → synth_market_views → emit_audit → END
--   react_upstream:         scan_upstream → emit_audit → END
--   refresh_sanctions_list: refresh_ofac → refresh_un → END
--   trade_book_recompute:   recompute_exposure → recompute_pnl → emit_audit → END
--   trade_idea_synthesize:  synth_ideas → emit_audit → END
--
-- 18 shosha mcp_tool_def rows already registered in dispatcher (iter22).
-- This migration adds the registry seed for the 18 NSIDs that consume them.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-intelIngestPrices',
   0, 0, 'com.etzhayyim.apps.shosha.intelIngestPrices', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha intel ingest prices.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/intelIngestPrices.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-intelIngestFreight',
   0, 0, 'com.etzhayyim.apps.shosha.intelIngestFreight', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha intel ingest freight.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/intelIngestFreight.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-marketViewSynth',
   0, 0, 'com.etzhayyim.apps.shosha.marketViewSynth', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha market-view synth.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/marketViewSynth.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-sanctionsRefreshOfac',
   0, 0, 'com.etzhayyim.apps.shosha.sanctionsRefreshOfac', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha sanctions refresh OFAC list.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/sanctionsRefreshOfac.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-sanctionsRefreshUn',
   0, 0, 'com.etzhayyim.apps.shosha.sanctionsRefreshUn', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha sanctions refresh UN list.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/sanctionsRefreshUn.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-exposureRecompute',
   0, 0, 'com.etzhayyim.apps.shosha.exposureRecompute', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha exposure recompute.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/exposureRecompute.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-pnlDailyRecompute',
   0, 0, 'com.etzhayyim.apps.shosha.pnlDailyRecompute', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha P&L daily recompute.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/pnlDailyRecompute.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-tradeSynth',
   0, 0, 'com.etzhayyim.apps.shosha.tradeSynth', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha trade idea synth.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/tradeSynth.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-dailyReportCompose',
   0, 0, 'com.etzhayyim.apps.shosha.dailyReportCompose', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha daily report compose.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/dailyReportCompose.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shosha-reactiveScanUpstream',
   0, 0, 'com.etzhayyim.apps.shosha.reactiveScanUpstream', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'shosha reactive scan upstream feeds.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shosha/reactiveScanUpstream.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

-- 6 v2 assistants
INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('shosha_daily_report.v2', 0, 0, 'shosha_daily_report.v2', 2, 'topology', NULL,
   '{"state_keys":["composeOut","auditOut","ok","error"],"entry":"compose_report","edges":[{"from":"compose_report","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}',
   'shosha daily report (topology v2, mcp_tool + audit.emit)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.shosha.etzhayyim.com'),
  ('shosha_market_intelligence.v2', 0, 0, 'shosha_market_intelligence.v2', 2, 'topology', NULL,
   '{"state_keys":["priceOut","freightOut","synthOut","auditOut","ok","error"],"entry":"ingest_prices","edges":[{"from":"ingest_prices","to":"ingest_freight"},{"from":"ingest_freight","to":"synth_market_views"},{"from":"synth_market_views","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}',
   'shosha market intelligence (topology v2, mcp_tool + audit.emit)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.shosha.etzhayyim.com'),
  ('shosha_react_upstream.v2', 0, 0, 'shosha_react_upstream.v2', 2, 'topology', NULL,
   '{"state_keys":["scanOut","auditOut","ok","error"],"entry":"scan_upstream","edges":[{"from":"scan_upstream","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}',
   'shosha react upstream (topology v2, mcp_tool + audit.emit)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.shosha.etzhayyim.com'),
  ('shosha_refresh_sanctions_list.v2', 0, 0, 'shosha_refresh_sanctions_list.v2', 2, 'topology', NULL,
   '{"state_keys":["ofacOut","unOut","ok","error"],"entry":"refresh_ofac","edges":[{"from":"refresh_ofac","to":"refresh_un"},{"from":"refresh_un","to":"END"}]}',
   'shosha refresh sanctions list (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.shosha.etzhayyim.com'),
  ('shosha_trade_book_recompute.v2', 0, 0, 'shosha_trade_book_recompute.v2', 2, 'topology', NULL,
   '{"state_keys":["exposureOut","pnlOut","auditOut","ok","error"],"entry":"recompute_exposure","edges":[{"from":"recompute_exposure","to":"recompute_pnl"},{"from":"recompute_pnl","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}',
   'shosha trade book recompute (topology v2, mcp_tool + audit.emit)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.shosha.etzhayyim.com'),
  ('shosha_trade_idea_synthesize.v2', 0, 0, 'shosha_trade_idea_synthesize.v2', 2, 'topology', NULL,
   '{"state_keys":["synthOut","auditOut","ok","error"],"entry":"synth_ideas","edges":[{"from":"synth_ideas","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}',
   'shosha trade idea synthesize (topology v2, mcp_tool + audit.emit)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.shosha.etzhayyim.com');

-- 16 mcp_tool nodes (10 actor tools + 5 audit.emit + 1 daily_report.compose_report ... wait,
-- actually per topology specs above:
--   daily_report:            2 nodes (compose, audit)
--   market_intelligence:     4 nodes (prices, freight, synth, audit)
--   react_upstream:          2 nodes (scan, audit)
--   refresh_sanctions_list:  2 nodes (ofac, un)            ← no audit
--   trade_book_recompute:    3 nodes (exposure, pnl, audit)
--   trade_idea_synthesize:   2 nodes (synth, audit)
--   total = 15 nodes (10 actor-task + 5 audit.emit)
INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  -- daily_report
  ('shosha_daily_report.v2:compose_report', 0, 0, 'shosha_daily_report.v2', 'compose_report',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.dailyReportCompose',
   '{"input_keys":[],"result_key":"composeOut","args":{"name":"com.etzhayyim.apps.shosha.dailyReportCompose"}}',
   '2026-05-09T00:00:00Z'),
  ('shosha_daily_report.v2:emit_audit', 0, 0, 'shosha_daily_report.v2', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:shosha.etzhayyim.com","collection":"com.etzhayyim.apps.shosha.audit","action":"daily_report"}}',
   '2026-05-09T00:00:00Z'),
  -- market_intelligence
  ('shosha_market_intelligence.v2:ingest_prices', 0, 0, 'shosha_market_intelligence.v2', 'ingest_prices',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.intelIngestPrices',
   '{"input_keys":[],"result_key":"priceOut","args":{"name":"com.etzhayyim.apps.shosha.intelIngestPrices"}}',
   '2026-05-09T00:00:00Z'),
  ('shosha_market_intelligence.v2:ingest_freight', 0, 0, 'shosha_market_intelligence.v2', 'ingest_freight',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.intelIngestFreight',
   '{"input_keys":[],"result_key":"freightOut","args":{"name":"com.etzhayyim.apps.shosha.intelIngestFreight"}}',
   '2026-05-09T00:00:00Z'),
  ('shosha_market_intelligence.v2:synth_market_views', 0, 0, 'shosha_market_intelligence.v2', 'synth_market_views',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.marketViewSynth',
   '{"input_keys":[],"result_key":"synthOut","args":{"name":"com.etzhayyim.apps.shosha.marketViewSynth"}}',
   '2026-05-09T00:00:00Z'),
  ('shosha_market_intelligence.v2:emit_audit', 0, 0, 'shosha_market_intelligence.v2', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:shosha.etzhayyim.com","collection":"com.etzhayyim.apps.shosha.audit","action":"market_intelligence"}}',
   '2026-05-09T00:00:00Z'),
  -- react_upstream
  ('shosha_react_upstream.v2:scan_upstream', 0, 0, 'shosha_react_upstream.v2', 'scan_upstream',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.reactiveScanUpstream',
   '{"input_keys":[],"result_key":"scanOut","args":{"name":"com.etzhayyim.apps.shosha.reactiveScanUpstream"}}',
   '2026-05-09T00:00:00Z'),
  ('shosha_react_upstream.v2:emit_audit', 0, 0, 'shosha_react_upstream.v2', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:shosha.etzhayyim.com","collection":"com.etzhayyim.apps.shosha.audit","action":"react_upstream"}}',
   '2026-05-09T00:00:00Z'),
  -- refresh_sanctions_list (no audit)
  ('shosha_refresh_sanctions_list.v2:refresh_ofac', 0, 0, 'shosha_refresh_sanctions_list.v2', 'refresh_ofac',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.sanctionsRefreshOfac',
   '{"input_keys":[],"result_key":"ofacOut","args":{"name":"com.etzhayyim.apps.shosha.sanctionsRefreshOfac"}}',
   '2026-05-09T00:00:00Z'),
  ('shosha_refresh_sanctions_list.v2:refresh_un', 0, 0, 'shosha_refresh_sanctions_list.v2', 'refresh_un',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.sanctionsRefreshUn',
   '{"input_keys":[],"result_key":"unOut","args":{"name":"com.etzhayyim.apps.shosha.sanctionsRefreshUn"}}',
   '2026-05-09T00:00:00Z'),
  -- trade_book_recompute
  ('shosha_trade_book_recompute.v2:recompute_exposure', 0, 0, 'shosha_trade_book_recompute.v2', 'recompute_exposure',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.exposureRecompute',
   '{"input_keys":[],"result_key":"exposureOut","args":{"name":"com.etzhayyim.apps.shosha.exposureRecompute"}}',
   '2026-05-09T00:00:00Z'),
  ('shosha_trade_book_recompute.v2:recompute_pnl', 0, 0, 'shosha_trade_book_recompute.v2', 'recompute_pnl',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.pnlDailyRecompute',
   '{"input_keys":[],"result_key":"pnlOut","args":{"name":"com.etzhayyim.apps.shosha.pnlDailyRecompute"}}',
   '2026-05-09T00:00:00Z'),
  ('shosha_trade_book_recompute.v2:emit_audit', 0, 0, 'shosha_trade_book_recompute.v2', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:shosha.etzhayyim.com","collection":"com.etzhayyim.apps.shosha.audit","action":"trade_book_recompute"}}',
   '2026-05-09T00:00:00Z'),
  -- trade_idea_synthesize
  ('shosha_trade_idea_synthesize.v2:synth_ideas', 0, 0, 'shosha_trade_idea_synthesize.v2', 'synth_ideas',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shosha.tradeSynth',
   '{"input_keys":[],"result_key":"synthOut","args":{"name":"com.etzhayyim.apps.shosha.tradeSynth"}}',
   '2026-05-09T00:00:00Z'),
  ('shosha_trade_idea_synthesize.v2:emit_audit', 0, 0, 'shosha_trade_idea_synthesize.v2', 'emit_audit',
   'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit',
   '{"input_keys":[],"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:shosha.etzhayyim.com","collection":"com.etzhayyim.apps.shosha.audit","action":"trade_idea_synthesize"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'shosha_daily_report.v2'           WHERE assistant_id = 'shosha_daily_report';
UPDATE vertex_langgraph_assistant SET superseded_by = 'shosha_market_intelligence.v2'    WHERE assistant_id = 'shosha_market_intelligence';
UPDATE vertex_langgraph_assistant SET superseded_by = 'shosha_react_upstream.v2'         WHERE assistant_id = 'shosha_react_upstream';
UPDATE vertex_langgraph_assistant SET superseded_by = 'shosha_refresh_sanctions_list.v2' WHERE assistant_id = 'shosha_refresh_sanctions_list';
UPDATE vertex_langgraph_assistant SET superseded_by = 'shosha_trade_book_recompute.v2'   WHERE assistant_id = 'shosha_trade_book_recompute';
UPDATE vertex_langgraph_assistant SET superseded_by = 'shosha_trade_idea_synthesize.v2'  WHERE assistant_id = 'shosha_trade_idea_synthesize';

FLUSH;
