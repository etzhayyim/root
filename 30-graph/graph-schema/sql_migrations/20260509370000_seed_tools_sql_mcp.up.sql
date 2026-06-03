-- ADR-2605082000 follow-up — register com.etzhayyim.tools.sql.query primitive.
--
-- Generic read-only SELECT primitive that wraps `pymagatama.db_alchemy.sa_query`.
-- Replaces per-actor sa_query py_primitive nodes (tsukuru_isic_pulse,
-- copyright_*, etzhayyimcojp_company_ops legal/finance agents, kaisya_member_assistant,
-- lawfirm_marketing_ops, warehouse_yard_optimizer, etc.) where the body is
-- a single bounded SELECT.
--
-- Strict guard at the dispatcher: only SELECT / WITH-CTE-SELECT statements
-- accepted; INSERT / UPDATE / DELETE / DDL rejected with error envelope.
-- Default row cap: 1000 (configurable per call via args.limit).

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-tools-sql-query',
   0, 0, 'com.etzhayyim.tools.sql.query', 'did:web:tsukuru.etzhayyim.com', 'tsukuru.etzhayyim.com', 'procedure',
   'Generic read-only SELECT — replaces per-actor sa_query py_primitive nodes.',
   '{"type":"object","properties":{"sql":{"type":"string"},"params":{"type":"object"},"limit":{"type":"integer"}},"required":["sql"]}',
   '{"type":"object","properties":{"rows":{"type":"array"},"rowCount":{"type":"integer"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/tools/sql/query.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
