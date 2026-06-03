-- ADR-2605082000 Phase A — shinka canonical migration.
--
-- Bulk-51 has 1 shinka_cron_tick assistant (1 node: shinka_tick →
-- task_shinka_tick). Earlier audit misclassified shinka as "primitive 未存在"
-- because the task lives in zeebe_worker_main.py rather than primitives/.
-- Iter39 confirmed 5 task_shinka_* functions exist; canonical actor exposes
-- all 5 (1 used by v2, 4 shelf-stocked).

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:shinka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shinka-tick',
   0, 0, 'com.etzhayyim.apps.shinka.tick', 'did:web:shinka.etzhayyim.com', 'shinka.etzhayyim.com', 'procedure',
   'shinka cron tick — call shinka_tick_actor SQL UDF for the target actor.',
   '{"type":"object","properties":{"actor":{"type":"string"}}}',
   '{"type":"object","properties":{"mood":{"type":"string"},"actions":{"type":"array"},"heartbeatWritten":{"type":"boolean"},"evolutionWritten":{"type":"boolean"},"tickMs":{"type":"integer"},"error":{"type":"string"}}}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shinka/tick.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shinka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shinka-loadAndResolve',
   0, 0, 'com.etzhayyim.apps.shinka.loadAndResolve', 'did:web:shinka.etzhayyim.com', 'shinka.etzhayyim.com', 'procedure',
   'shinka load + resolve actor evolution graph (shelf-stocked).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shinka/loadAndResolve.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shinka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shinka-compose',
   0, 0, 'com.etzhayyim.apps.shinka.compose', 'did:web:shinka.etzhayyim.com', 'shinka.etzhayyim.com', 'procedure',
   'shinka compose actor mood / action plan (shelf-stocked).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shinka/compose.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shinka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shinka-writeHeartbeat',
   0, 0, 'com.etzhayyim.apps.shinka.writeHeartbeat', 'did:web:shinka.etzhayyim.com', 'shinka.etzhayyim.com', 'procedure',
   'shinka write heartbeat (shelf-stocked).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shinka/writeHeartbeat.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:shinka.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-shinka-emitEvolution',
   0, 0, 'com.etzhayyim.apps.shinka.emitEvolution', 'did:web:shinka.etzhayyim.com', 'shinka.etzhayyim.com', 'procedure',
   'shinka emit evolution event (shelf-stocked).',
   '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/shinka/emitEvolution.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('shinka_cron_tick.v2', 0, 0, 'shinka_cron_tick.v2', 2, 'topology', NULL,
   '{"state_keys":["actor","tickOut","ok","error"],"entry":"shinka_tick","edges":[{"from":"shinka_tick","to":"END"}]}',
   'shinka cron tick (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.shinka.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('shinka_cron_tick.v2:shinka_tick', 0, 0, 'shinka_cron_tick.v2', 'shinka_tick',
   'mcp_tool', 'mcp://com.etzhayyim.apps.shinka.tick',
   '{"input_keys":["actor"],"result_key":"tickOut","args":{"name":"com.etzhayyim.apps.shinka.tick"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'shinka_cron_tick.v2'
 WHERE assistant_id = 'shinka_cron_tick';

FLUSH;
