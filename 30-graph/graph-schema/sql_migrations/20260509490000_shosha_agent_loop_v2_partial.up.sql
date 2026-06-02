-- ADR-2605082000 Phase E1 — partial decomposition pilot.
--
-- Target: shosha_agent_loop (3 live py_primitive nodes from bulk-51).
-- Excluded from prior shosha_canonical_v2 batch with the note "fetchContext
-- + callLlm are self_logic per iter25 NO_TASK_IMPORT spot-check".
--
-- This is the first Phase E pilot — the goal is to validate the standard
-- chain template (LLM-side data-only, py_primitive exception for
-- domain-specific dynamic SQL) on a small (3-node) assistant before
-- attacking the 6+ node assistants.
--
-- Decomposition outcome:
--   fetch_context  py_primitive  KEPT (3 dynamic-WHERE SQL queries +
--                                multi-row text assembly = legitimate
--                                exception per ADR Phase E §Known
--                                constraints #4). Extended in this commit
--                                to also produce `_userMessage` so the
--                                downstream mcp_tool can consume it.
--   call_llm       mcp_tool      RETIRED → mcp://com.etzhayyim.tools.llm.chat
--                                (input_paths renames _userMessage→user)
--   emit_audit     mcp_tool      RETIRED → mcp://com.etzhayyim.tools.audit.emit
--
-- Net: 3 py_primitive → 1 py_primitive + 2 mcp_tool.
-- Audit live py_primitive count: -2 (delta visible after re-run).

INSERT INTO vertex_langgraph_assistant (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at) VALUES ('shosha_agent_loop.v2', 0, 0, 'shosha_agent_loop.v2', 2, 'topology', NULL, '{"state_keys":["prompt","tier","maxTokens","commodityFocus","_context","_userMessage","intelRowsUsed","marketViewRowsUsed","exposureRowsUsed","llmOut","auditOut","ok","error"],"entry":"fetch_context","edges":[{"from":"fetch_context","to":"call_llm"},{"from":"call_llm","to":"emit_audit"},{"from":"emit_audit","to":"END"}]}', 'shosha agent loop (Phase E1 partial decomposition: fetch_context py_primitive exception + 2 mcp_tool nodes)', '2026-05-09T07:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('shosha_agent_loop.v2:fetch_context', 0, 0, 'shosha_agent_loop.v2', 'fetch_context', 'py_primitive', 'pymagatama.langgraph_graphs.shosha_agent_loop:fetch_context', NULL, '2026-05-09T07:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('shosha_agent_loop.v2:call_llm', 0, 0, 'shosha_agent_loop.v2', 'call_llm', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_keys":[],"input_paths":{"user":"_userMessage","tier":"tier","maxTokens":"maxTokens"},"result_key":"llmOut","args":{"name":"com.etzhayyim.tools.llm.chat","system":"You are 商社 (shosha.etzhayyim.com), an autonomous AI sogo-shosha agent. You have read access to recent market intel, market views, and open exposure. Be concise, factual, and acknowledge uncertainty. Default to Japanese unless the user writes English. Keep replies under 600 tokens.","temperature":0.3}}', '2026-05-09T07:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('shosha_agent_loop.v2:emit_audit', 0, 0, 'shosha_agent_loop.v2', 'emit_audit', 'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit', '{"input_keys":[],"input_paths":{"recordJson":"llmOut.result"},"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:shosha.etzhayyim.com","collection":"com.etzhayyim.apps.shosha.agentLoop","action":"create"}}', '2026-05-09T07:00:00Z');

INSERT INTO vertex_langgraph_deployment (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at) VALUES ('langgraph.builtin.shosha_agent_loop.v2', 0, 0, 'langgraph.builtin.shosha_agent_loop.v2', 'shosha_agent_loop.v2', 2, 'active', 1, '2026-05-09T07:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'shosha_agent_loop.v2'
 WHERE assistant_id = 'shosha_agent_loop';

FLUSH;
