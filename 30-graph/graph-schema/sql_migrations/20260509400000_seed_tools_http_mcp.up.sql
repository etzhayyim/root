-- ADR-2605082000 follow-up — register com.etzhayyim.tools.http.fetch primitive.
--
-- Generic HTTP fetch (read-only by default). Replaces per-actor httpx
-- py_primitive nodes (copyright_*, isbn_*, public_malak_ads_*, ...).
-- Write methods (POST/PUT/DELETE) require explicit args.allowWrite=true.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-tools-http-fetch',
   0, 0, 'com.etzhayyim.tools.http.fetch', 'did:web:copyright.etzhayyim.com', 'copyright.etzhayyim.com', 'procedure',
   'Generic HTTP fetch — replaces per-actor httpx py_primitive nodes.',
   '{"type":"object","properties":{"url":{"type":"string"},"method":{"type":"string"},"headers":{"type":"object"},"body":{"type":"string"},"timeout":{"type":"number"},"allowWrite":{"type":"boolean"}},"required":["url"]}',
   '{"type":"object","properties":{"status":{"type":"integer"},"headers":{"type":"object"},"body":{"type":"string"},"isText":{"type":"boolean"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/tools/http/fetch.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
