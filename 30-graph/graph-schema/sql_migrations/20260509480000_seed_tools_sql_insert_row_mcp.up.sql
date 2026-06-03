-- ADR-2605082000 Phase E0 — register com.etzhayyim.tools.sql.insert_row primitive.
--
-- Dynamic-column INSERT primitive. Bridges the LLM-supervisor decomposition
-- pattern (Phase E §Standard Decomposition Template): LLM returns
-- `db_writes: [{table, row}, ...]`, foreach iterates, each iteration calls
-- this primitive with one item. Auto-derives vertex_id from a template if
-- the row doesn't supply one.
--
-- Safety: table + column names must match `^[a-zA-Z_][a-zA-Z0-9_]*$`.
-- Values are bound via SQLAlchemy parameters (never string-interpolated).

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-tools-sql-insert_row',
   0, 0, 'com.etzhayyim.tools.sql.insert_row', 'did:web:tsukuru.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Dynamic-column INSERT — table + row dict + optional vertex_id_template (Phase E0).',
   '{"type":"object","properties":{"table":{"type":"string","pattern":"^[a-zA-Z_][a-zA-Z0-9_]*$"},"row":{"type":"object","additionalProperties":{"type":["string","number","boolean","null"]}},"vertex_id_template":{"type":"string"},"owner_did":{"type":"string"},"collection":{"type":"string"}},"required":["table","row"]}',
   '{"type":"object","properties":{"vertexId":{"type":"string"},"ok":{"type":"boolean"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/tools/sql/insertRow.json',
   'anon', 'anon', '', '2026-05-09T06:00:00Z');

FLUSH;
