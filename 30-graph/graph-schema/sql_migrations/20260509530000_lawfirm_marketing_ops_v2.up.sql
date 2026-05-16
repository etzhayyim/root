-- ADR-2605082000 Phase E3 — lawfirm-marketing-ops decomposition.
--
-- Target: lawfirm-marketing-ops (9 live py_primitive nodes from bulk-51).
-- Pattern: supervisor (prefix routing) → 6 specialist agents → compliance_gate
-- (LLM rate + threshold) → emit_audit (2-table persist) → END.
--
-- Decomposition outcome (5 mcp_tool + 4 py_primitive):
--   supervisor          py_primitive  KEPT (prefix-map + keyword fallback,
--                                          emits clean `kind` field for
--                                          Phase D2 field-routed edge)
--   content   →  content_call_llm   mcp_tool  RETIRED → llm.chat (user_template)
--   social    →  social_call_llm    mcp_tool  RETIRED → llm.chat
--   outreach  →  outreach_call_llm  mcp_tool  RETIRED → llm.chat
--   platform  →  platform_call_llm  mcp_tool  RETIRED → llm.chat
--   event     →  event_call_llm     mcp_tool  RETIRED → llm.chat
--   analytics           py_primitive  KEPT (DB query → KPI snapshot →
--                                          LLM synthesize; mixed DB+LLM
--                                          exception, same justification
--                                          as compliance_gate)
--   compliance_gate     py_primitive  KEPT (platform-brand disclaimer
--                                          rule + advocate-brand LLM
--                                          rate-and-route → exception)
--   emit_audit          py_primitive  KEPT (writes 2 vertex tables with
--                                          derived vids + monotonic ts;
--                                          not a single-record audit.emit
--                                          shape)
--
-- Net: 9 py_primitive → 5 mcp_tool + 4 py_primitive. -5 live py_primitive.
--
-- compliance_gate + emit_audit were extended in lawfirm_marketing_ops.py
-- with `_resolve_asset_from_envelope(state)` so they can read body_md /
-- asset_kind / title from `state.<domain>LlmOut.result.content` when the
-- upstream node is mcp_tool ai.gftd.tools.llm.chat. Legacy state fields
-- still take priority — v1 unit tests stay green.
--
-- Routing: supervisor's Phase D2 field-based conditional edge
-- (field=`kind`, paths→domain) is preserved; paths point to the new
-- `<domain>_call_llm` nodes (analytics path stays `analytics`).

INSERT INTO vertex_langgraph_assistant (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at) VALUES ('lawfirm-marketing-ops.v2', 0, 0, 'lawfirm-marketing-ops.v2', 2, 'topology', NULL, '{"state_keys":["task_type","brand","audience","topic","payload","schedule_at","requester_did","thread_id","kind","routing_reason","contentLlmOut","socialLlmOut","outreachLlmOut","platformLlmOut","eventLlmOut","asset_kind","title","body_md","target_url","asset_uris","compliance_check","compliance_notes","compliance_score","summary","ok","error"],"entry":"supervisor","edges":[{"from":"content_call_llm","to":"compliance_gate"},{"from":"social_call_llm","to":"compliance_gate"},{"from":"outreach_call_llm","to":"compliance_gate"},{"from":"platform_call_llm","to":"compliance_gate"},{"from":"event_call_llm","to":"compliance_gate"},{"from":"analytics","to":"compliance_gate"},{"from":"compliance_gate","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"supervisor","field":"kind","paths":{"content":"content_call_llm","social":"social_call_llm","outreach":"outreach_call_llm","platform":"platform_call_llm","analytics":"analytics","event":"event_call_llm","unknown":"content_call_llm"},"default":"content_call_llm"}]}', 'lawfirm-marketing-ops (Phase E3: 5 LLM nodes mcp_tool + supervisor/analytics/compliance_gate/emit_audit py_primitive exceptions)', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('lawfirm-marketing-ops.v2:supervisor', 0, 0, 'lawfirm-marketing-ops.v2', 'supervisor', 'py_primitive', 'pymagatama.langgraph_graphs.lawfirm_marketing_ops:supervisor', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('lawfirm-marketing-ops.v2:content_call_llm', 0, 0, 'lawfirm-marketing-ops.v2', 'content_call_llm', 'mcp_tool', 'mcp://ai.gftd.tools.llm.chat', '{"input_paths":{"topic":"topic","audience":"audience","payload":"payload","task_type":"task_type"},"result_key":"contentLlmOut","args":{"name":"ai.gftd.tools.llm.chat","tier":"balanced","system":"You are the content agent for lawfirm.gftd.ai. Brand: ADVOCATE (k-bakshi personal practice) means BCI Rule 36 strict — information-only, no soliciting, no success rate claims, no testimonials.\n\nDraft an EDUCATIONAL blog article in English on the given topic. Audience: typically NRI / Indian SMB / Japan-India cross-border tech firms.\n\nRequirements:\n- 800-1500 words markdown\n- Clear H2/H3 structure\n- Cite Indian statute / case law where relevant\n- Include \"Disclaimer: This article is for general information only and does not constitute legal advice. Consult a qualified advocate for specific matters.\" at the bottom\n\nOutput ONLY the article body in markdown, NO meta commentary.","user_template":"Topic: {topic}\nAudience: {audience}\nReference context: {payload}","maxTokens":2400,"temperature":0.4}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('lawfirm-marketing-ops.v2:social_call_llm', 0, 0, 'lawfirm-marketing-ops.v2', 'social_call_llm', 'mcp_tool', 'mcp://ai.gftd.tools.llm.chat', '{"input_paths":{"topic":"topic","audience":"audience","payload":"payload"},"result_key":"socialLlmOut","args":{"name":"ai.gftd.tools.llm.chat","tier":"balanced","system":"You are the social agent for lawfirm.gftd.ai (advocate brand). Draft a LinkedIn post (k-bakshi personal account) on the given topic.\n\nRequirements:\n- 150-400 words, plain text (no markdown)\n- Educational / observational tone\n- ZERO solicitation language (\"hire me\", \"contact for representation\" forbidden)\n- Optional 2-4 hashtags at the end\n- May include link to the lawfirm.gftd.ai/insights blog if relevant\n- Sign off as \"— Kunal\"","user_template":"Topic: {topic}\nAudience: {audience}\nContext: {payload}","maxTokens":700,"temperature":0.5}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('lawfirm-marketing-ops.v2:outreach_call_llm', 0, 0, 'lawfirm-marketing-ops.v2', 'outreach_call_llm', 'mcp_tool', 'mcp://ai.gftd.tools.llm.chat', '{"input_paths":{"topic":"topic","audience":"audience","payload":"payload"},"result_key":"outreachLlmOut","args":{"name":"ai.gftd.tools.llm.chat","tier":"balanced","system":"You are the outreach agent. Draft a warm-intro email for k-bakshi to send to a mid-tier Indian law firm partner.\n\nThis is NOT a cold sales mail — it''s a peer introduction with two angles:\n(1) Bakshi & Partners LLP (incorporation in progress) for referral collaboration,\n(2) lawfirm.gftd.ai SaaS pilot (3-month no-cost) — ONLY mention if asked.\n\nRequirements:\n- 200-350 words\n- English, professional, warm\n- ZERO BCI Rule 36 violation: never claim success rates, never compare to other firms negatively, never use \"best/leading/top\" superlatives\n- End with \"Best, Kunal Bakshi\" + role line\n- Include a clear ask (30 min meeting, Bangalore in-person preferred)","user_template":"Target firm + partner: {audience}\nSpecific angle / their practice: {topic}\nReference context: {payload}","maxTokens":900,"temperature":0.4}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('lawfirm-marketing-ops.v2:platform_call_llm', 0, 0, 'lawfirm-marketing-ops.v2', 'platform_call_llm', 'mcp_tool', 'mcp://ai.gftd.tools.llm.chat', '{"input_paths":{"topic":"topic","audience":"audience","payload":"payload","task_type":"task_type"},"result_key":"platformLlmOut","args":{"name":"ai.gftd.tools.llm.chat","tier":"balanced","system":"You are the platform marketing agent for lawfirm.gftd.ai SaaS, operated by amanomibashira. Brand = PLATFORM, NOT advocate practice. Commercial marketing copy is OK (this is a tech operator product page, not advocate solicitation).\n\nDraft the requested platform marketing copy.\n\nRequirements:\n- Match the asset_kind in task_type (landing-page section / tweet / one-pager).\n- Word count: tweet 220 chars / landing section 200-400 words / one-pager 600-900 words\n- Highlight differentiation: multilingual intake, cross-border auto-route, BCI Rule 36 + DPDP Act 2023-grade encryption, BPMN audit trail\n- Include \"amanomibashira is a platform operator. lawfirm.gftd.ai SaaS does not provide legal advice; the customer firm''s advocates retain all professional responsibility.\" disclaimer at the bottom\n- ZERO advocate-practice language (no \"we represent clients\", etc.)","user_template":"Asset type: {topic}\nAudience: {audience}\nContext: {payload}","maxTokens":1500,"temperature":0.4}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('lawfirm-marketing-ops.v2:analytics', 0, 0, 'lawfirm-marketing-ops.v2', 'analytics', 'py_primitive', 'pymagatama.langgraph_graphs.lawfirm_marketing_ops:analytics_agent', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('lawfirm-marketing-ops.v2:event_call_llm', 0, 0, 'lawfirm-marketing-ops.v2', 'event_call_llm', 'mcp_tool', 'mcp://ai.gftd.tools.llm.chat', '{"input_paths":{"topic":"topic","payload":"payload"},"result_key":"eventLlmOut","args":{"name":"ai.gftd.tools.llm.chat","tier":"balanced","system":"You are the event prep agent. Draft a 1-page briefing for k-bakshi attending a conference / meetup / podcast.\n\nInclude:\n- Talking points (3-5 bullet, BCI Rule 36-safe)\n- 2-3 questions to ask other speakers\n- 5 target conversations (audience profile + opening line)\n- Reciprocal value (what we offer in conversations)\n- Disclaimer of advocate practice (do not solicit during the event)\n\nOutput markdown.","user_template":"Event: {topic}\nContext: {payload}","maxTokens":1500,"temperature":0.4}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('lawfirm-marketing-ops.v2:compliance_gate', 0, 0, 'lawfirm-marketing-ops.v2', 'compliance_gate', 'py_primitive', 'pymagatama.langgraph_graphs.lawfirm_marketing_ops:compliance_gate', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('lawfirm-marketing-ops.v2:emit_audit', 0, 0, 'lawfirm-marketing-ops.v2', 'emit_audit', 'py_primitive', 'pymagatama.langgraph_graphs.lawfirm_marketing_ops:emit_audit', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_deployment (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at) VALUES ('langgraph.builtin.lawfirm-marketing-ops.v2', 0, 0, 'langgraph.builtin.lawfirm-marketing-ops.v2', 'lawfirm-marketing-ops.v2', 2, 'active', 1, '2026-05-09T09:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'lawfirm-marketing-ops.v2'
 WHERE assistant_id = 'lawfirm-marketing-ops';

FLUSH;
