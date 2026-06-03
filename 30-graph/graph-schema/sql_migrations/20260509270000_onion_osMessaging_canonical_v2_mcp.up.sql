-- ADR-2605082000 Phase A — onion + osMessaging canonical migration (batch).
--
-- Both bulk-51 assistants are 2-node linear ingest pipelines:
--   onion_crawl_seeds:                queue_seeds   → process_queue → END
--   os_messaging_crawl_open_channels: queue_seed_runs → process_queue → END
--
-- Each node binds task_<snake> from its primitives module (no actor prefix
-- because they are originally single-purpose pipelines). Method names
-- mirror the task names directly.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:onion.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-onion-queueSeeds',
   0, 0, 'com.etzhayyim.apps.onion.queueSeeds', 'did:web:onion.etzhayyim.com', 'onion.etzhayyim.com', 'procedure',
   'Queue Tor / onion seeds for crawling.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/onion/queueSeeds.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:onion.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-onion-processQueue',
   0, 0, 'com.etzhayyim.apps.onion.processQueue', 'did:web:onion.etzhayyim.com', 'onion.etzhayyim.com', 'procedure',
   'Process the onion crawl queue.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/onion/processQueue.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:os-messaging.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-osMessaging-queueSeedRuns',
   0, 0, 'com.etzhayyim.apps.osMessaging.queueSeedRuns', 'did:web:os-messaging.etzhayyim.com', 'os-messaging.etzhayyim.com', 'procedure',
   'Queue OS messaging seed runs.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/osMessaging/queueSeedRuns.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:os-messaging.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-osMessaging-processQueue',
   0, 0, 'com.etzhayyim.apps.osMessaging.processQueue', 'did:web:os-messaging.etzhayyim.com', 'os-messaging.etzhayyim.com', 'procedure',
   'Process the OS messaging open-channels queue.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/osMessaging/processQueue.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('onion_crawl_seeds.v2', 0, 0, 'onion_crawl_seeds.v2', 2, 'topology', NULL,
   '{"state_keys":["queueOut","processOut","ok","error"],"entry":"queue_seeds","edges":[{"from":"queue_seeds","to":"process_queue"},{"from":"process_queue","to":"END"}]}',
   'onion crawl seeds (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.onion.etzhayyim.com'),
  ('os_messaging_crawl_open_channels.v2', 0, 0, 'os_messaging_crawl_open_channels.v2', 2, 'topology', NULL,
   '{"state_keys":["queueOut","processOut","ok","error"],"entry":"queue_seed_runs","edges":[{"from":"queue_seed_runs","to":"process_queue"},{"from":"process_queue","to":"END"}]}',
   'os messaging crawl open channels (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.os-messaging.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('onion_crawl_seeds.v2:queue_seeds', 0, 0, 'onion_crawl_seeds.v2', 'queue_seeds',
   'mcp_tool', 'mcp://com.etzhayyim.apps.onion.queueSeeds',
   '{"input_keys":[],"result_key":"queueOut","args":{"name":"com.etzhayyim.apps.onion.queueSeeds"}}',
   '2026-05-09T00:00:00Z'),
  ('onion_crawl_seeds.v2:process_queue', 0, 0, 'onion_crawl_seeds.v2', 'process_queue',
   'mcp_tool', 'mcp://com.etzhayyim.apps.onion.processQueue',
   '{"input_keys":[],"result_key":"processOut","args":{"name":"com.etzhayyim.apps.onion.processQueue"}}',
   '2026-05-09T00:00:00Z'),
  ('os_messaging_crawl_open_channels.v2:queue_seed_runs', 0, 0, 'os_messaging_crawl_open_channels.v2', 'queue_seed_runs',
   'mcp_tool', 'mcp://com.etzhayyim.apps.osMessaging.queueSeedRuns',
   '{"input_keys":[],"result_key":"queueOut","args":{"name":"com.etzhayyim.apps.osMessaging.queueSeedRuns"}}',
   '2026-05-09T00:00:00Z'),
  ('os_messaging_crawl_open_channels.v2:process_queue', 0, 0, 'os_messaging_crawl_open_channels.v2', 'process_queue',
   'mcp_tool', 'mcp://com.etzhayyim.apps.osMessaging.processQueue',
   '{"input_keys":[],"result_key":"processOut","args":{"name":"com.etzhayyim.apps.osMessaging.processQueue"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'onion_crawl_seeds.v2'
 WHERE assistant_id = 'onion_crawl_seeds';
UPDATE vertex_langgraph_assistant SET superseded_by = 'os_messaging_crawl_open_channels.v2'
 WHERE assistant_id = 'os_messaging_crawl_open_channels';

FLUSH;
