-- ADR-2605082000 Phase E2 — webmk_create_proposal decomposition.
--
-- Target: webmk_create_proposal (6 live py_primitive nodes from bulk-51).
-- Pattern: 4-stage LLM pipeline (research → competitors → strategy → copy)
-- + quality_gate (LLM rate + threshold routing) + store_proposal (single
-- INSERT with id derivation).
--
-- Decomposition outcome:
--   research_company     mcp_tool   RETIRED → llm.chat (user_template)
--   analyze_competitors  mcp_tool   RETIRED → llm.chat (user_template)
--   generate_strategy    mcp_tool   RETIRED → llm.chat (user_template)
--   generate_copy        mcp_tool   RETIRED → llm.chat (user_template)
--   quality_gate         py_primitive  KEPT (LLM call + JSON parse +
--                                      threshold→nextRoute logic = ADR
--                                      Phase E §Known constraints exception
--                                      pending E3 threshold-route primitive)
--   store_proposal       py_primitive  KEPT (single INSERT with sha256 id
--                                      derivation, time stamping = exception)
--
-- Net: 6 py_primitive → 4 mcp_tool + 2 py_primitive. -4 live py_primitive.
--
-- Note: kind=mcp_tool relies on Phase E2's user_template extension to
-- task_llm_chat (renders user from state-derived vars without a preceding
-- transform.map step). All 4 LLM nodes use input_paths to pass state slices
-- as template vars.
--
-- Routing: quality_gate's field-based conditional edge (Phase D2) is
-- preserved unchanged in the v2 config.

INSERT INTO vertex_langgraph_assistant (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at) VALUES ('webmk_create_proposal.v2', 0, 0, 'webmk_create_proposal.v2', 2, 'topology', NULL, '{"state_keys":["proposalId","clientName","websiteUrl","industry","targetAudience","budgetJpy","deliveryEmail","createAdCampaign","companyContextOut","competitorSummaryOut","strategyOut","copyOut","company_context","competitor_summary","strategy_json","copy_markdown","quality_score","retry_count","nextRoute","ok","error"],"entry":"research_company","edges":[{"from":"research_company","to":"analyze_competitors"},{"from":"analyze_competitors","to":"generate_strategy"},{"from":"generate_strategy","to":"generate_copy"},{"from":"generate_copy","to":"quality_gate"},{"from":"store_proposal","to":"END"}],"conditional_edges":[{"from":"quality_gate","field":"nextRoute","paths":{"store":"store_proposal","retry":"generate_strategy"},"default":"store"}]}', 'webmk createProposal (Phase E2: 4 LLM nodes mcp_tool + quality_gate / store_proposal py_primitive exception)', '2026-05-09T08:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('webmk_create_proposal.v2:research_company', 0, 0, 'webmk_create_proposal.v2', 'research_company', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"websiteUrl":"websiteUrl","industry":"industry"},"result_key":"companyContextOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"fast","system":"You are a marketing researcher. Respond with concise JSON only.","user_template":"Analyze this company URL: {websiteUrl}\nIndustry: {industry}\n\nReturn JSON with keys: offering, targetSegment, marketingTone, angles[]","maxTokens":600,"temperature":0.3}}', '2026-05-09T08:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('webmk_create_proposal.v2:analyze_competitors', 0, 0, 'webmk_create_proposal.v2', 'analyze_competitors', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"clientName":"clientName","industry":"industry","companyContext":"companyContextOut.result.content"},"result_key":"competitorSummaryOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"fast","system":"You are a competitive intelligence analyst. Respond with concise JSON only.","user_template":"Client: {clientName}\nIndustry: {industry}\nContext: {companyContext}\n\nIdentify 3 likely competitors. Return JSON: competitors[{{name,positioning,keywords[],opportunity}}], mainGap","maxTokens":700,"temperature":0.3}}', '2026-05-09T08:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('webmk_create_proposal.v2:generate_strategy', 0, 0, 'webmk_create_proposal.v2', 'generate_strategy', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"clientName":"clientName","websiteUrl":"websiteUrl","industry":"industry","budgetJpy":"budgetJpy","companyContext":"companyContextOut.result.content","competitorSummary":"competitorSummaryOut.result.content"},"result_key":"strategyOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"balanced","system":"You are a senior digital marketing strategist. Respond with JSON only.","user_template":"Client: {clientName}\nWebsite: {websiteUrl}\nIndustry: {industry}\nBudget JPY: {budgetJpy}\n\nResearch:\n{companyContext}\n\nCompetitors:\n{competitorSummary}\n\nReturn JSON: {{executiveSummary, channels[{{name,priority,rationale,kpis[]}}], contentThemes[], sixMonthMilestones[{{month,goal,metric}}], estimatedRoi}}","maxTokens":1200,"temperature":0.4}}', '2026-05-09T08:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('webmk_create_proposal.v2:generate_copy', 0, 0, 'webmk_create_proposal.v2', 'generate_copy', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"clientName":"clientName","websiteUrl":"websiteUrl","strategy":"strategyOut.result.content"},"result_key":"copyOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"balanced","system":"You are a copywriter. Format output in Markdown.","user_template":"Client: {clientName} ({websiteUrl})\nStrategy: {strategy}\n\nWrite:\n## Hero Headlines (3)\n## Sub-headline\n## SNS Posts (Instagram/X/LinkedIn)\n## Email Subject Lines (A/B)\n## Google Ads Headlines (3, ≤30 chars)\n## CTA Options (3)","maxTokens":1000,"temperature":0.5}}', '2026-05-09T08:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('webmk_create_proposal.v2:quality_gate', 0, 0, 'webmk_create_proposal.v2', 'quality_gate', 'py_primitive', 'pymagatama.langgraph_graphs.webmk_proposal:quality_gate', NULL, '2026-05-09T08:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('webmk_create_proposal.v2:store_proposal', 0, 0, 'webmk_create_proposal.v2', 'store_proposal', 'py_primitive', 'pymagatama.langgraph_graphs.webmk_proposal:store_proposal', NULL, '2026-05-09T08:00:00Z');

INSERT INTO vertex_langgraph_deployment (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at) VALUES ('langgraph.builtin.webmk_create_proposal.v2', 0, 0, 'langgraph.builtin.webmk_create_proposal.v2', 'webmk_create_proposal.v2', 2, 'active', 1, '2026-05-09T08:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'webmk_create_proposal.v2'
 WHERE assistant_id = 'webmk_create_proposal';

FLUSH;
