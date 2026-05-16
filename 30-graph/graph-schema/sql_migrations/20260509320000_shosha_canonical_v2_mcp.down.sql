UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id IN (
   'shosha_daily_report', 'shosha_market_intelligence', 'shosha_react_upstream',
   'shosha_refresh_sanctions_list', 'shosha_trade_book_recompute', 'shosha_trade_idea_synthesize'
 );

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id LIKE 'shosha_%.v2';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id LIKE 'shosha_%.v2';

DELETE FROM vertex_mcp_tool_def
 WHERE nsid IN (
   'ai.gftd.apps.shosha.intelIngestPrices', 'ai.gftd.apps.shosha.intelIngestFreight',
   'ai.gftd.apps.shosha.marketViewSynth', 'ai.gftd.apps.shosha.sanctionsRefreshOfac',
   'ai.gftd.apps.shosha.sanctionsRefreshUn', 'ai.gftd.apps.shosha.exposureRecompute',
   'ai.gftd.apps.shosha.pnlDailyRecompute', 'ai.gftd.apps.shosha.tradeSynth',
   'ai.gftd.apps.shosha.dailyReportCompose', 'ai.gftd.apps.shosha.reactiveScanUpstream'
 );

FLUSH;
