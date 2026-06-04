-- ADR-2605082000 Phase E3 — kaisya-member-assistant decomposition.
--
-- Target: kaisya-member-assistant (8 live py_primitive nodes from bulk-51).
--
-- Decomposition outcome:
--   resolve_member       py_primitive  KEPT (UPN→DID lookup + dynamic SQL +
--                                       sets nextRoute. Phase D2 field-routed.
--                                       Legitimate exception per ADR Phase E
--                                       §Known constraints #4)
--   load_context         py_primitive  KEPT (dynamic-WHERE SQL on
--                                       vertex_etzhayyimcojp_raci + multi-row text
--                                       assembly = exception #4)
--   supervisor           py_primitive  KEPT — LLM JSON classifier producing
--                                       state.route. The mcp_tool envelope
--                                       (`com.etzhayyim.tools.llm.chat`) only
--                                       exposes `.result.content` as raw
--                                       string; routing on a parsed JSON
--                                       field would require either a
--                                       downstream parse-py_primitive (no
--                                       net code-island win) or extending
--                                       the LLM tool to expose parsed JSON
--                                       (out of scope for E3). Phase D2
--                                       already routes on `field: route`;
--                                       behavior preserved.
--   company_ops          py_primitive  KEPT — cross-graph dispatch via
--                                       `etzhayyimcojp_company_ops.build_graph().invoke()`
--                                       (legitimate exception, side effect)
--   lawfirm_marketing    py_primitive  KEPT — cross-graph dispatch via
--                                       `lawfirm_marketing_ops.build_graph().invoke()`
--                                       + heuristic task_type derivation
--                                       (legitimate exception, side effect)
--   lawfirm_sales        py_primitive  KEPT — RACI-gated SQL read +
--                                       can_mutate computation (dynamic
--                                       SQL = exception #4)
--   direct_reply         mcp_tool      RETIRED → mcp://com.etzhayyim.tools.llm.chat
--                                       (user_template renders state-derived
--                                       vars; result_key=directReplyLlmOut).
--                                       The downstream py_primitive
--                                       `emit_audit` was extended to read
--                                       reply_text from
--                                       `directReplyLlmOut.result.content`
--                                       and to compute
--                                       `requires_human_approval` from
--                                       `state.route == "escalate"`. Legacy
--                                       state.reply_text fallback preserved
--                                       so v1 deployments keep working.
--   emit_audit           py_primitive  KEPT — single INSERT into
--                                       vertex_repo_commit. The audit
--                                       payload is composed from 6 distinct
--                                       state fields (channel/session_id/
--                                       route/reason/sub_summary/reply
--                                       length); no clean state field
--                                       carries the full record shape, so
--                                       converting to
--                                       mcp://com.etzhayyim.tools.audit.emit
--                                       would require a new prepare_audit
--                                       py_primitive upstream — net 0 gain.
--                                       (legitimate exception, side effect)
--
-- Net: 8 py_primitive → 7 py_primitive + 1 mcp_tool. -1 live code-island.
--
-- Routing: both Phase D2 field-routed conditional edges are preserved
-- unchanged (resolve_member→nextRoute, supervisor→route).

INSERT INTO vertex_langgraph_assistant (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at) VALUES ('kaisya-member-assistant.v2', 0, 0, 'kaisya-member-assistant.v2', 2, 'topology', NULL, '{"state_keys":["user_upn","session_id","user_message","history","channel","member_did","member_name","member_role","raci_summary","route","nextRoute","routing_reason","sub_result","sub_summary","directReplyLlmOut","reply_text","citations","requires_human_approval","ok","error"],"entry":"resolve_member","edges":[{"from":"load_context","to":"supervisor"},{"from":"company_ops","to":"direct_reply"},{"from":"lawfirm_marketing","to":"direct_reply"},{"from":"lawfirm_sales","to":"direct_reply"},{"from":"direct_reply","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"resolve_member","field":"nextRoute","paths":{"denied":"direct_reply","load_context":"load_context"},"default":"load_context"},{"from":"supervisor","field":"route","paths":{"company_ops":"company_ops","lawfirm_marketing":"lawfirm_marketing","lawfirm_sales":"lawfirm_sales","direct_reply":"direct_reply","escalate":"direct_reply"},"default":"direct_reply"}]}', 'kaisya-member-assistant (Phase E3: direct_reply mcp_tool + 7 py_primitive exceptions)', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('kaisya-member-assistant.v2:resolve_member', 0, 0, 'kaisya-member-assistant.v2', 'resolve_member', 'py_primitive', 'pymagatama.langgraph_graphs.kaisya_member_assistant:resolve_member', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('kaisya-member-assistant.v2:load_context', 0, 0, 'kaisya-member-assistant.v2', 'load_context', 'py_primitive', 'pymagatama.langgraph_graphs.kaisya_member_assistant:load_context', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('kaisya-member-assistant.v2:supervisor', 0, 0, 'kaisya-member-assistant.v2', 'supervisor', 'py_primitive', 'pymagatama.langgraph_graphs.kaisya_member_assistant:supervisor', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('kaisya-member-assistant.v2:company_ops', 0, 0, 'kaisya-member-assistant.v2', 'company_ops', 'py_primitive', 'pymagatama.langgraph_graphs.kaisya_member_assistant:company_ops_dispatch', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('kaisya-member-assistant.v2:lawfirm_marketing', 0, 0, 'kaisya-member-assistant.v2', 'lawfirm_marketing', 'py_primitive', 'pymagatama.langgraph_graphs.kaisya_member_assistant:lawfirm_marketing_dispatch', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('kaisya-member-assistant.v2:lawfirm_sales', 0, 0, 'kaisya-member-assistant.v2', 'lawfirm_sales', 'py_primitive', 'pymagatama.langgraph_graphs.kaisya_member_assistant:lawfirm_sales_dispatch', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('kaisya-member-assistant.v2:direct_reply', 0, 0, 'kaisya-member-assistant.v2', 'direct_reply', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"member_name":"member_name","member_role":"member_role","raci_summary":"raci_summary","user_message":"user_message","sub_summary":"sub_summary","route":"route"},"result_key":"directReplyLlmOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"balanced","system":"You are the kaisya.etzhayyim.com member chat assistant. Reply directly to the user''s message. Be specific. Cite RACI scope when declining or escalating. Tone: professional, concise, Japanese OK. If the user is asking about something outside their RACI, name the member who IS responsible (e.g. \"PwC clearance is owned by k-bakshi + j-kawasaki — would you like me to draft a request on your behalf?\").","user_template":"Member {member_name} ({member_role})\nRACI scope:\n{raci_summary}\n\nMessage: {user_message}\n\nRoute: {route}\nSub-graph summary (if any): {sub_summary}","maxTokens":1000,"temperature":0.4}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('kaisya-member-assistant.v2:emit_audit', 0, 0, 'kaisya-member-assistant.v2', 'emit_audit', 'py_primitive', 'pymagatama.langgraph_graphs.kaisya_member_assistant:emit_audit', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_deployment (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at) VALUES ('langgraph.builtin.kaisya-member-assistant.v2', 0, 0, 'langgraph.builtin.kaisya-member-assistant.v2', 'kaisya-member-assistant.v2', 2, 'active', 1, '2026-05-09T09:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'kaisya-member-assistant.v2'
 WHERE assistant_id = 'kaisya-member-assistant';

FLUSH;
