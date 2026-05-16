-- ADR-2605082000 follow-up — register ai.gftd.tools.llm.chat primitive.
--
-- Generic LLM chat primitive that wraps task_generic_llm_chat. Replaces
-- per-actor pure-LLM py_primitive nodes (animeka_autopilot.generate_*
-- etc.) with a single data-resolved tool whose system/user prompts
-- live in topology.config.args (= data, ADR-2605082000 §2.6 pattern).
--
-- actor_host: animeka.gftd.ai (first heavy consumer). UPDATE later if a
-- dedicated tools-llm Worker is created.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:animeka.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-tools-llm-chat',
   0, 0, 'ai.gftd.tools.llm.chat', 'did:web:animeka.gftd.ai', 'animeka.gftd.ai', 'procedure',
   'Generic free-form LLM chat — replaces per-actor LLM-only py_primitive nodes.',
   '{"type":"object","properties":{"tier":{"type":"string"},"system":{"type":"string"},"user":{"type":"string"},"maxTokens":{"type":"integer"},"temperature":{"type":"number"}},"required":["user"]}',
   '{"type":"object","properties":{"content":{"type":"string"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/ai/gftd/tools/llm/chat.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
