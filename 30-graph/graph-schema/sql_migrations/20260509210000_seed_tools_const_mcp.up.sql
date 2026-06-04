-- ADR-2605082000 follow-up — register the generic com.etzhayyim.tools.const.echo
-- primitive in vertex_mcp_tool_def.
--
-- This is the data-driven replacement for identity / no-op nodes (the
-- prototypical case is ki.cycle's `skip_bloom`). With this row in place,
-- a topology node binds as:
--
--   kind=mcp_tool
--   ref=mcp://com.etzhayyim.tools.const.echo
--   config={"input_keys":[],"result_key":"<state_field>",
--           "args":{"name":"com.etzhayyim.tools.const.echo",
--                   "constant":{"bloomSkipped":true,"bloomId":null}}}
--
-- Note: `constant` is supplied via config.args (not state) because the
-- whole point of an identity node is to ignore state. ``make_mcp_tool_node``
-- already passes ``config.args.*`` keys through as part of the envelope's
-- top-level params (alongside ``name``); the dispatcher routes them as
-- kwargs to ``task_echo``.
--
-- actor_host hosting strategy: for now any Worker that proxies the MCP
-- envelope can serve generic primitives. We default to ``ki.etzhayyim.com``
-- (first consumer). Once a dedicated ``tools.etzhayyim.com`` Worker exists,
-- a follow-up UPDATE flips actor_host without touching topology rows.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:ki.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-tools-const-echo',
   0, 0,
   'com.etzhayyim.tools.const.echo', 'did:web:ki.etzhayyim.com', 'ki.etzhayyim.com', 'procedure',
   'Identity / constant-return primitive for LangGraph topology no-op nodes.',
   '{"type":"object","properties":{"constant":{"type":"object"}},"required":["constant"]}',
   '{"type":"object","description":"Echoes the input constant verbatim."}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/tools/const/echo.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
