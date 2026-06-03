-- ADR-2605082000 follow-up — register com.etzhayyim.tools.json.extract primitive.
--
-- Safe dotted-path JSON navigator. Bridges http.fetch body strings and
-- downstream nodes that need a sub-tree (e.g. Crossref `message.items`).
-- No eval / JSONPath / JMESPath — defensive subset only.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-tools-json-extract',
   0, 0, 'com.etzhayyim.tools.json.extract', 'did:web:copyright.etzhayyim.com', 'copyright.etzhayyim.com', 'procedure',
   'Generic JSON extract — safe dotted path navigator (a.b[2].c, a.*).',
   '{"type":"object","properties":{"json":{},"path":{"type":"string"},"default":{}},"required":["json","path"]}',
   '{"type":"object","properties":{"value":{},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/tools/json/extract.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
