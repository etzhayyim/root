UPDATE vertex_langgraph_assistant SET superseded_by = NULL
 WHERE assistant_id IN (
   'shosha_daily_report', 'shosha_market_intelligence', 'shosha_react_upstream',
   'shosha_refresh_sanctions_list', 'shosha_trade_book_recompute', 'shosha_trade_idea_synthesize'
 );

DELETE FROM vertex_langgraph_assistant_node WHERE assistant_id LIKE 'shosha_%.v2';
DELETE FROM vertex_langgraph_assistant      WHERE assistant_id LIKE 'shosha_%.v2';

DELETE FROM vertex_mcp_tool_def
 WHERE nsid IN (
   'com.etzhayyim.apps.shosha.intelIngestPrices', 'com.etzhayyim.apps.shosha.intelIngestFreight',
   'com.etzhayyim.apps.shosha.marketViewSynth', 'com.etzhayyim.apps.shosha.sanctionsRefreshOfac',
   'com.etzhayyim.apps.shosha.sanctionsRefreshUn', 'com.etzhayyim.apps.shosha.exposureRecompute',
   'com.etzhayyim.apps.shosha.pnlDailyRecompute', 'com.etzhayyim.apps.shosha.tradeSynth',
   'com.etzhayyim.apps.shosha.dailyReportCompose', 'com.etzhayyim.apps.shosha.reactiveScanUpstream'
 );

FLUSH;
