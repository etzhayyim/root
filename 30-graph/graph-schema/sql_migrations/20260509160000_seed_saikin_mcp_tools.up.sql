-- ADR-2605082000 PoC seed — register the 5 saikin tools in vertex_mcp_tool_def.
--
-- These rows are the registry SSoT consumed by `_resolve_mcp_nsid` in
-- pymagatama/langgraph_node_resolvers.py: SELECT actor_host FROM
-- vertex_mcp_tool_def WHERE nsid = $1 AND enabled = true. Once these rows
-- exist, a topology node bound as `kind=mcp_tool` `ref=mcp://com.etzhayyim.apps.saikin.<m>`
-- resolves to https://saikin.etzhayyim.com/xrpc/com.etzhayyim.mcp.message at runtime.
--
-- Schema columns mirror sync-mcp-registry.py output (the canonical sync
-- script). vertex_id slug uses dot→dash per its convention. input_schema
-- and output_schema are pulled from the corresponding lexicon JSON
-- (`00-contracts/lexicons/com/etzhayyim/apps/saikin/*.json`); kept compact here
-- for migration readability.
--
-- This is a *seed* row — sync-mcp-registry.py will reconcile/overwrite it
-- when the full pipeline runs (it computes schema_hash and may bump the
-- version). PK = vertex_id, so re-INSERT is RW implicit upsert.
--
-- Runtime end-to-end note: the saikin Worker today proxies XRPC to a
-- Python dispatcher (60-apps/etzhayyim-project-saikin/src/app.ts → DISPATCHER_URL).
-- The dispatcher does NOT yet handle com.etzhayyim.mcp.message envelopes — that
-- wire-up is the next migration step (deps.toml saikin-cycle-mcp-migration §2).

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord,
   nsid, actor_did, actor_host, lexicon_type, description,
   input_schema, output_schema,
   visibility, version, enabled, source_path,
   org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-probeEnvironment',
   0, 0,
   'com.etzhayyim.apps.saikin.probeEnvironment', 'did:web:saikin.etzhayyim.com', 'saikin.etzhayyim.com', 'query',
   'Scan external data sources for novel signals (bacterial chemotaxis).',
   '{"type":"object"}',
   '{"type":"object","properties":{"signalCount":{"type":"integer"},"signals":{"type":"array"},"error":{"type":"string"}},"required":["signalCount","signals"]}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/saikin/probeEnvironment.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),

  ('at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-transferSignal',
   0, 0,
   'com.etzhayyim.apps.saikin.transferSignal', 'did:web:saikin.etzhayyim.com', 'saikin.etzhayyim.com', 'procedure',
   'Transfer a novel signal to a peer actor (horizontal gene transfer).',
   '{"type":"object","properties":{"signals":{"type":"array"},"signalId":{"type":"string"},"targetActorDid":{"type":"string"}}}',
   '{"type":"object","properties":{"transferId":{"type":"string"},"status":{"type":"string"},"signalId":{"type":"string"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/saikin/transferSignal.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),

  ('at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-formColony',
   0, 0,
   'com.etzhayyim.apps.saikin.formColony', 'did:web:saikin.etzhayyim.com', 'saikin.etzhayyim.com', 'procedure',
   'Group related signals into a colony (biofilm formation).',
   '{"type":"object","properties":{"signalIds":{"type":"array","items":{"type":"string"}}},"required":["signalIds"]}',
   '{"type":"object","properties":{"colonyId":{"type":"string"},"memberCount":{"type":"integer"},"error":{"type":"string"}},"required":["colonyId","memberCount"]}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/saikin/formColony.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),

  ('at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-handoffToKi',
   0, 0,
   'com.etzhayyim.apps.saikin.handoffToKi', 'did:web:saikin.etzhayyim.com', 'saikin.etzhayyim.com', 'procedure',
   'Hand off a colony or signal to ki for vertical synthesis.',
   '{"type":"object","properties":{"colonyId":{"type":"string"},"signalId":{"type":"string"}}}',
   '{"type":"object","properties":{"kiAbsorbId":{"type":"string"},"kiAbsorbVertexId":{"type":"string"},"error":{"type":"string"}},"required":["kiAbsorbId","kiAbsorbVertexId"]}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/saikin/handoffToKi.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),

  ('at://did:web:saikin.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-saikin-lyse',
   0, 0,
   'com.etzhayyim.apps.saikin.lyse', 'did:web:saikin.etzhayyim.com', 'saikin.etzhayyim.com', 'procedure',
   'Release a fully-transferred signal (bacterial autolysis).',
   '{"type":"object","properties":{"signalId":{"type":"string"},"reason":{"type":"string"}},"required":["signalId"]}',
   '{"type":"object","properties":{"lysed":{"type":"boolean"},"releasedAt":{"type":"string"},"error":{"type":"string"}}}',
   'public', 1, TRUE,
   '00-contracts/lexicons/com/etzhayyim/apps/saikin/lyse.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

FLUSH;
