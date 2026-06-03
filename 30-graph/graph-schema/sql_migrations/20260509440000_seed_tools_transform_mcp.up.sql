-- ADR-2605082000 follow-up — register com.etzhayyim.tools.transform.map primitive.
--
-- Per-row declarative transform. Bridges fetched arrays (http.fetch +
-- json.extract output) and downstream sql.exec INSERT rows that need
-- restructured fields. Replaces per-actor `_<actor>_row(item)` Python
-- transform functions in copyright_*, isbn_*, animeka_*, etc.
--
-- Mapping grammar (defensive subset, no eval / JSONPath):
--   "$.path"             — copy from input row at dotted path
--   {const: <any>}       — literal constant
--   {fmt: "{a.b}-x"}     — format with {paths} substituted
--   {path:"$.x", default:?} — path with fallback

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-tools-transform-map',
   0, 0, 'com.etzhayyim.tools.transform.map', 'did:web:copyright.etzhayyim.com', 'copyright.etzhayyim.com', 'procedure',
   'Generic per-row declarative transform — replaces _row() py_primitive.',
   '{"type":"object","properties":{"input":{"type":"array"},"mapping":{"type":"object"},"defaults":{"type":"object"}},"required":["input","mapping"]}',
   '{"type":"object","properties":{"rows":{"type":"array"},"rowCount":{"type":"integer"},"skipped":{"type":"integer"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/tools/transform/map.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
