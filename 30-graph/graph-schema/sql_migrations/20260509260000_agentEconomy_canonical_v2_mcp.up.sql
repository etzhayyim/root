-- ADR-2605082000 Phase A — agentEconomy canonical migration.
--
-- bulk-51 has 1 agent_runtime_lease_autopilot assistant (1 node:
-- autopilot_tick → task_agent_runtime_autopilot_tick). The canonical
-- actor `agentEconomy` registers 9 tools from
-- pymagatama.primitives.agent_economy (only one is currently consumed by
-- a topology assistant; the remaining 8 are runtime-callable directly via
-- MCP envelope and will become topology nodes when later flows author them).
--
-- Pattern: 1 bulk-51 assistant → 1 canonical actor with N tools.
-- Demonstrates that the data-layer migration registers the FULL tool
-- surface even when only a subset has assistant consumers today.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:agent-economy.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-agentEconomy-runtimeQuote',
   0, 0, 'com.etzhayyim.apps.agentEconomy.runtimeQuote', 'did:web:agent-economy.etzhayyim.com', 'agent-economy.etzhayyim.com', 'procedure',
   'Quote runtime cost for an actor lease.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/agentEconomy/runtimeQuote.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:agent-economy.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-agentEconomy-runtimeReserve',
   0, 0, 'com.etzhayyim.apps.agentEconomy.runtimeReserve', 'did:web:agent-economy.etzhayyim.com', 'agent-economy.etzhayyim.com', 'procedure',
   'Reserve runtime budget for an actor.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/agentEconomy/runtimeReserve.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:agent-economy.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-agentEconomy-runtimeRenew',
   0, 0, 'com.etzhayyim.apps.agentEconomy.runtimeRenew', 'did:web:agent-economy.etzhayyim.com', 'agent-economy.etzhayyim.com', 'procedure',
   'Renew an existing runtime reservation.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/agentEconomy/runtimeRenew.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:agent-economy.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-agentEconomy-runtimeHibernate',
   0, 0, 'com.etzhayyim.apps.agentEconomy.runtimeHibernate', 'did:web:agent-economy.etzhayyim.com', 'agent-economy.etzhayyim.com', 'procedure',
   'Hibernate an actor (release runtime, keep state).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/agentEconomy/runtimeHibernate.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:agent-economy.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-agentEconomy-runtimeAutopilotTick',
   0, 0, 'com.etzhayyim.apps.agentEconomy.runtimeAutopilotTick', 'did:web:agent-economy.etzhayyim.com', 'agent-economy.etzhayyim.com', 'procedure',
   'Autopilot tick — sweep leases for renew/hibernate decisions.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/agentEconomy/runtimeAutopilotTick.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:agent-economy.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-agentEconomy-incomeRecord',
   0, 0, 'com.etzhayyim.apps.agentEconomy.incomeRecord', 'did:web:agent-economy.etzhayyim.com', 'agent-economy.etzhayyim.com', 'procedure',
   'Record an income event for an actor.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/agentEconomy/incomeRecord.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:agent-economy.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-agentEconomy-usageRecord',
   0, 0, 'com.etzhayyim.apps.agentEconomy.usageRecord', 'did:web:agent-economy.etzhayyim.com', 'agent-economy.etzhayyim.com', 'procedure',
   'Record a usage event for an actor.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/agentEconomy/usageRecord.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:agent-economy.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-agentEconomy-slashRecord',
   0, 0, 'com.etzhayyim.apps.agentEconomy.slashRecord', 'did:web:agent-economy.etzhayyim.com', 'agent-economy.etzhayyim.com', 'procedure',
   'Record a slash event (governance penalty).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/agentEconomy/slashRecord.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:agent-economy.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-agentEconomy-spawnChildOrg',
   0, 0, 'com.etzhayyim.apps.agentEconomy.spawnChildOrg', 'did:web:agent-economy.etzhayyim.com', 'agent-economy.etzhayyim.com', 'procedure',
   'Spawn a child org from a parent agent (governance).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/agentEconomy/spawnChildOrg.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('agent_runtime_lease_autopilot.v2', 0, 0, 'agent_runtime_lease_autopilot.v2', 2, 'topology', NULL,
   '{"state_keys":["tickOut","ok","error"],"entry":"autopilot_tick","edges":[{"from":"autopilot_tick","to":"END"}]}',
   'agent runtime lease autopilot (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.agent-economy.etzhayyim.com');

INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('agent_runtime_lease_autopilot.v2:autopilot_tick', 0, 0, 'agent_runtime_lease_autopilot.v2', 'autopilot_tick',
   'mcp_tool', 'mcp://com.etzhayyim.apps.agentEconomy.runtimeAutopilotTick',
   '{"input_keys":[],"result_key":"tickOut","args":{"name":"com.etzhayyim.apps.agentEconomy.runtimeAutopilotTick"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'agent_runtime_lease_autopilot.v2'
 WHERE assistant_id = 'agent_runtime_lease_autopilot';

FLUSH;
