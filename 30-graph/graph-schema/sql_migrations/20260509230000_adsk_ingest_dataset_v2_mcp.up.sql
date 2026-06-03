-- ADR-2605082000 Phase A — adsk_ingest_dataset.v2 with mcp_tool node.
--
-- 3rd ready-to-flip actor (after saikin + ki). First demonstration of the
-- override-convention path:
--   com.etzhayyim.apps.adsk.datasetIngestAll   →   pymagatama.primitives.adsk:task_adsk_dataset_ingest_all
-- See `mcp_dispatch._DEFAULT_ACTORS` `module` + `fn_template` override entry
-- (committed in iter17). bulk-51's original `adsk_ingest_dataset` row is the
-- only py_primitive in this assistant — once flipped, this assistant is fully
-- data-resolved.
--
-- This migration:
--   1. Inserts the vertex_mcp_tool_def row for com.etzhayyim.apps.adsk.datasetIngestAll
--      (actor_host=adsk.etzhayyim.com)
--   2. Inserts assistant adsk_ingest_dataset.v2 (kind=topology, mcp_tool node)
--   3. Marks v1 (the bulk-51 row) as superseded
--
-- Pin flip is a separate migration with the operator gate.
--
-- RUNTIME CAVEAT: adsk.etzhayyim.com Worker does NOT exist yet. The MCP envelope
-- POST to https://adsk.etzhayyim.com/xrpc/com.etzhayyim.mcp.message will fail at edge.
-- This migration is **data-only** — the lexicon, seed, and topology rows
-- describe the intended target. Before the pin flip is applicable, either:
--   (a) Create 60-apps/etzhayyim-project-adsk/src/app.ts following the
--       saikin/ki Worker template (NSID_PREFIX + MCP_NSID branches), OR
--   (b) UPDATE vertex_mcp_tool_def SET actor_host='saikin.etzhayyim.com' WHERE
--       nsid='com.etzhayyim.apps.adsk.datasetIngestAll'  -- route via existing
--       proxy until adsk Worker is deployed.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:adsk.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-adsk-datasetIngestAll',
   0, 0,
   'com.etzhayyim.apps.adsk.datasetIngestAll', 'did:web:adsk.etzhayyim.com', 'adsk.etzhayyim.com', 'procedure',
   'Re-ingest stale rows from vertex_hf_dataset (R/P30D autopilot).',
   '{"type":"object","properties":{"staleSeconds":{"type":"integer"},"perDatasetLimit":{"type":"integer"}}}',
   '{"type":"object","properties":{"summary":{"type":"array"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/adsk/datasetIngestAll.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord,
   assistant_id, version, kind, factory_path, spec, description, created_at,
   checkpointer_mode, authored_by)
VALUES (
  'adsk_ingest_dataset.v2', 0, 0,
  'adsk_ingest_dataset.v2', 2, 'topology', NULL,
  '{"state_keys":["staleSeconds","perDatasetLimit","ingestOut","ok","error"],"entry":"ingest_all","edges":[{"from":"ingest_all","to":"END"}]}',
  'adsk dataset re-ingest autopilot (topology v2, mcp_tool node)',
  '2026-05-09T00:00:00Z',
  'rw_vertex',
  'did:web:agent.adsk.etzhayyim.com'
);

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('adsk_ingest_dataset.v2:ingest_all', 0, 0,
   'adsk_ingest_dataset.v2', 'ingest_all',
   'mcp_tool', 'mcp://com.etzhayyim.apps.adsk.datasetIngestAll',
   '{"input_keys":["staleSeconds","perDatasetLimit"],"result_key":"ingestOut","args":{"name":"com.etzhayyim.apps.adsk.datasetIngestAll"}}',
   '2026-05-09T00:00:00Z');

-- Mark the bulk-51 v1 as superseded (lineage trace).
UPDATE vertex_langgraph_assistant
   SET superseded_by = 'adsk_ingest_dataset.v2'
 WHERE assistant_id = 'adsk_ingest_dataset';

FLUSH;
