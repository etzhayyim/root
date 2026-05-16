-- ADR-2605082000 follow-up — register ai.gftd.tools.sql.exec primitive.
--
-- Generic write SQL primitive (INSERT / UPDATE / UPSERT only).
-- Strict guards: rejects SELECT (use sql.query) / DELETE / DROP /
-- TRUNCATE / GRANT / REVOKE / CREATE / ALTER. Requires args.confirmWrite=true.
-- If args.rows is supplied, runs sa_executemany batch mode.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:tsukuru.gftd.ai/ai.gftd.mcp.toolDef/ai-gftd-tools-sql-exec',
   0, 0, 'ai.gftd.tools.sql.exec', 'did:web:tsukuru.gftd.ai', 'tsukuru.gftd.ai', 'procedure',
   'Generic write SQL — INSERT / UPDATE / UPSERT, with strict guards + confirmWrite.',
   '{"type":"object","properties":{"sql":{"type":"string"},"params":{"type":"object"},"rows":{"type":"array"},"confirmWrite":{"type":"boolean"}},"required":["sql","confirmWrite"]}',
   '{"type":"object","properties":{"rowCount":{"type":"integer"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/ai/gftd/tools/sql/exec.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
