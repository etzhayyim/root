-- ADR-2605082000 follow-up — register com.etzhayyim.tools.audit.emit primitive.
--
-- Generic OCEL emitter that replaces per-actor `emit_audit` py_primitive
-- nodes (shosha_*, isbn_*, animeka_*, ki_cycle, etc.). Once seeded, those
-- nodes can rebind to:
--
--   kind=mcp_tool
--   ref=mcp://com.etzhayyim.tools.audit.emit
--   config={"input_keys":[],"result_key":"auditOut",
--           "args":{"name":"com.etzhayyim.tools.audit.emit",
--                   "repo":"did:web:<actor>.etzhayyim.com",
--                   "collection":"com.etzhayyim.apps.<actor>.audit",
--                   "action":"<verb>"}}
--
-- actor_host follows the const.echo convention: the first heavy consumer
-- (shosha) hosts the primitive at shosha.etzhayyim.com. Future move to a
-- dedicated tools-audit Worker is a single UPDATE.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:shosha.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-tools-audit-emit',
   0, 0, 'com.etzhayyim.tools.audit.emit', 'did:web:shosha.etzhayyim.com', 'shosha.etzhayyim.com', 'procedure',
   'Generic OCEL audit emitter — replaces per-actor emit_audit py_primitive.',
   '{"type":"object","properties":{"repo":{"type":"string"},"collection":{"type":"string"},"rkey":{"type":"string"},"action":{"type":"string"},"recordJson":{"type":"object"}},"required":["repo","collection","action"]}',
   '{"type":"object","properties":{"vertexId":{"type":"string"},"rkey":{"type":"string"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/tools/audit/emit.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
