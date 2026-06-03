-- ADR-2605082000 Phase A — wellbecoming canonical migration (largest batch).
--
-- 9 bulk-51 assistants (10 nodes total) → canonical `wellbecoming` actor with
-- 11 mcp_tool_def rows. Tool surface mapping (per iter23 dispatcher entry):
--
--   bulk-51 node                   → canonical method
--   ----------------------------     ----------------
--   influence_propagate            → beliefInfluencePropagate
--   noise_inject                   → beliefNoiseInject
--   restoring_capture              → beliefRestoringCapture
--   detect_bottleneck              → bottleneckDetect
--   floor_check                    → floorCheck
--   floor_alert                    → floorAlert
--   minimax_sweep                  → minimaxSweep
--   proactive_connect              → proactiveConnect
--   process_mining                 → processMiningAnalyze
--   trust_weight_update            → trustWeightUpdate
--   (also seeded: agentLoop tool — shelf-stocking, no v2 consumer yet)
--
-- floor_violation_alert preserves its conditional Python router for now —
-- ADR-2605082000 §3 Rego/DMN conversion is a follow-up phase.

INSERT INTO vertex_mcp_tool_def
  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,
   description, input_schema, output_schema, visibility, version, enabled,
   source_path, org_id, user_id, actor_id, created_at)
VALUES
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-agentLoop',
   0, 0, 'com.etzhayyim.apps.wellbecoming.agentLoop', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Wellbecoming agent loop (shelf-stocking).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/agentLoop.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-bottleneckDetect',
   0, 0, 'com.etzhayyim.apps.wellbecoming.bottleneckDetect', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Detect bottlenecks in wellbecoming flows.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/bottleneckDetect.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-proactiveConnect',
   0, 0, 'com.etzhayyim.apps.wellbecoming.proactiveConnect', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Proactively connect wellbecoming peers.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/proactiveConnect.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-floorCheck',
   0, 0, 'com.etzhayyim.apps.wellbecoming.floorCheck', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Check wellbecoming floor violations in a time window.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/floorCheck.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-floorAlert',
   0, 0, 'com.etzhayyim.apps.wellbecoming.floorAlert', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Emit wellbecoming floor-violation alert.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/floorAlert.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-minimaxSweep',
   0, 0, 'com.etzhayyim.apps.wellbecoming.minimaxSweep', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Wellbecoming minimax sweep.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/minimaxSweep.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-beliefInfluencePropagate',
   0, 0, 'com.etzhayyim.apps.wellbecoming.beliefInfluencePropagate', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Propagate belief influence in the wellbecoming graph.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/beliefInfluencePropagate.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-beliefNoiseInject',
   0, 0, 'com.etzhayyim.apps.wellbecoming.beliefNoiseInject', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Inject belief noise (perturbation experiment).', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/beliefNoiseInject.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-beliefRestoringCapture',
   0, 0, 'com.etzhayyim.apps.wellbecoming.beliefRestoringCapture', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Capture wellbecoming belief restoring events.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/beliefRestoringCapture.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-trustWeightUpdate',
   0, 0, 'com.etzhayyim.apps.wellbecoming.trustWeightUpdate', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Update wellbecoming trust weights.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/trustWeightUpdate.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z'),
  ('at://did:web:wellbecoming.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-wellbecoming-processMiningAnalyze',
   0, 0, 'com.etzhayyim.apps.wellbecoming.processMiningAnalyze', 'did:web:wellbecoming.etzhayyim.com', 'wellbecoming.etzhayyim.com', 'procedure',
   'Wellbecoming process-mining analyze.', '{"type":"object"}', '{"type":"object"}',
   'public', 1, TRUE, '00-contracts/lexicons/com/etzhayyim/apps/wellbecoming/processMiningAnalyze.json',
   'anon', 'anon', '', '2026-05-09T00:00:00Z');

-- 9 v2 assistants (one per bulk-51 sibling). Each is single-node except
-- floor_violation_alert which keeps its conditional router.
INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path,
   spec, description, created_at, checkpointer_mode, authored_by)
VALUES
  ('wellbecoming_belief_influence_propagate.v2', 0, 0, 'wellbecoming_belief_influence_propagate.v2', 2, 'topology', NULL,
   '{"state_keys":["out","ok","error"],"entry":"influence_propagate","edges":[{"from":"influence_propagate","to":"END"}]}',
   'wellbecoming belief influence propagate (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.wellbecoming.etzhayyim.com'),
  ('wellbecoming_belief_noise_inject.v2', 0, 0, 'wellbecoming_belief_noise_inject.v2', 2, 'topology', NULL,
   '{"state_keys":["out","ok","error"],"entry":"noise_inject","edges":[{"from":"noise_inject","to":"END"}]}',
   'wellbecoming belief noise inject (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.wellbecoming.etzhayyim.com'),
  ('wellbecoming_belief_restoring_capture.v2', 0, 0, 'wellbecoming_belief_restoring_capture.v2', 2, 'topology', NULL,
   '{"state_keys":["out","ok","error"],"entry":"restoring_capture","edges":[{"from":"restoring_capture","to":"END"}]}',
   'wellbecoming belief restoring capture (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.wellbecoming.etzhayyim.com'),
  ('wellbecoming_detect_bottleneck.v2', 0, 0, 'wellbecoming_detect_bottleneck.v2', 2, 'topology', NULL,
   '{"state_keys":["out","ok","error"],"entry":"detect_bottleneck","edges":[{"from":"detect_bottleneck","to":"END"}]}',
   'wellbecoming detect bottleneck (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.wellbecoming.etzhayyim.com'),
  ('wellbecoming_floor_violation_alert.v2', 0, 0, 'wellbecoming_floor_violation_alert.v2', 2, 'topology', NULL,
   '{"state_keys":["window_minutes","floor_violation_count","violation_ids","has_violations","alert_emitted","ok","error"],"entry":"floor_check","edges":[{"from":"floor_alert","to":"END"}],"conditional_edges":[{"from":"floor_check","router":"pymagatama.langgraph_graphs.wellbecoming_floor_violation_alert:_route_after_check","paths":{"floor_alert":"floor_alert","__end__":"END"}}]}',
   'wellbecoming floor violation alert (topology v2, mcp_tool nodes + conditional)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.wellbecoming.etzhayyim.com'),
  ('wellbecoming_minimax_sweep.v2', 0, 0, 'wellbecoming_minimax_sweep.v2', 2, 'topology', NULL,
   '{"state_keys":["out","ok","error"],"entry":"minimax_sweep","edges":[{"from":"minimax_sweep","to":"END"}]}',
   'wellbecoming minimax sweep (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.wellbecoming.etzhayyim.com'),
  ('wellbecoming_proactive_connect.v2', 0, 0, 'wellbecoming_proactive_connect.v2', 2, 'topology', NULL,
   '{"state_keys":["out","ok","error"],"entry":"proactive_connect","edges":[{"from":"proactive_connect","to":"END"}]}',
   'wellbecoming proactive connect (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.wellbecoming.etzhayyim.com'),
  ('wellbecoming_process_mining.v2', 0, 0, 'wellbecoming_process_mining.v2', 2, 'topology', NULL,
   '{"state_keys":["out","ok","error"],"entry":"process_mining","edges":[{"from":"process_mining","to":"END"}]}',
   'wellbecoming process mining (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.wellbecoming.etzhayyim.com'),
  ('wellbecoming_trust_weight_update.v2', 0, 0, 'wellbecoming_trust_weight_update.v2', 2, 'topology', NULL,
   '{"state_keys":["out","ok","error"],"entry":"trust_weight_update","edges":[{"from":"trust_weight_update","to":"END"}]}',
   'wellbecoming trust weight update (topology v2, mcp_tool)', '2026-05-09T00:00:00Z',
   'rw_vertex', 'did:web:agent.wellbecoming.etzhayyim.com');

-- 10 mcp_tool nodes
INSERT INTO vertex_langgraph_assistant_node
  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)
VALUES
  ('wellbecoming_belief_influence_propagate.v2:influence_propagate', 0, 0, 'wellbecoming_belief_influence_propagate.v2', 'influence_propagate',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.beliefInfluencePropagate',
   '{"input_keys":[],"result_key":"out","args":{"name":"com.etzhayyim.apps.wellbecoming.beliefInfluencePropagate"}}',
   '2026-05-09T00:00:00Z'),
  ('wellbecoming_belief_noise_inject.v2:noise_inject', 0, 0, 'wellbecoming_belief_noise_inject.v2', 'noise_inject',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.beliefNoiseInject',
   '{"input_keys":[],"result_key":"out","args":{"name":"com.etzhayyim.apps.wellbecoming.beliefNoiseInject"}}',
   '2026-05-09T00:00:00Z'),
  ('wellbecoming_belief_restoring_capture.v2:restoring_capture', 0, 0, 'wellbecoming_belief_restoring_capture.v2', 'restoring_capture',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.beliefRestoringCapture',
   '{"input_keys":[],"result_key":"out","args":{"name":"com.etzhayyim.apps.wellbecoming.beliefRestoringCapture"}}',
   '2026-05-09T00:00:00Z'),
  ('wellbecoming_detect_bottleneck.v2:detect_bottleneck', 0, 0, 'wellbecoming_detect_bottleneck.v2', 'detect_bottleneck',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.bottleneckDetect',
   '{"input_keys":[],"result_key":"out","args":{"name":"com.etzhayyim.apps.wellbecoming.bottleneckDetect"}}',
   '2026-05-09T00:00:00Z'),
  ('wellbecoming_floor_violation_alert.v2:floor_check', 0, 0, 'wellbecoming_floor_violation_alert.v2', 'floor_check',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.floorCheck',
   '{"input_keys":["window_minutes"],"result_key":"floor_violation_count","args":{"name":"com.etzhayyim.apps.wellbecoming.floorCheck"}}',
   '2026-05-09T00:00:00Z'),
  ('wellbecoming_floor_violation_alert.v2:floor_alert', 0, 0, 'wellbecoming_floor_violation_alert.v2', 'floor_alert',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.floorAlert',
   '{"input_keys":["violation_ids"],"result_key":"alert_emitted","args":{"name":"com.etzhayyim.apps.wellbecoming.floorAlert"}}',
   '2026-05-09T00:00:00Z'),
  ('wellbecoming_minimax_sweep.v2:minimax_sweep', 0, 0, 'wellbecoming_minimax_sweep.v2', 'minimax_sweep',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.minimaxSweep',
   '{"input_keys":[],"result_key":"out","args":{"name":"com.etzhayyim.apps.wellbecoming.minimaxSweep"}}',
   '2026-05-09T00:00:00Z'),
  ('wellbecoming_proactive_connect.v2:proactive_connect', 0, 0, 'wellbecoming_proactive_connect.v2', 'proactive_connect',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.proactiveConnect',
   '{"input_keys":[],"result_key":"out","args":{"name":"com.etzhayyim.apps.wellbecoming.proactiveConnect"}}',
   '2026-05-09T00:00:00Z'),
  ('wellbecoming_process_mining.v2:process_mining', 0, 0, 'wellbecoming_process_mining.v2', 'process_mining',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.processMiningAnalyze',
   '{"input_keys":[],"result_key":"out","args":{"name":"com.etzhayyim.apps.wellbecoming.processMiningAnalyze"}}',
   '2026-05-09T00:00:00Z'),
  ('wellbecoming_trust_weight_update.v2:trust_weight_update', 0, 0, 'wellbecoming_trust_weight_update.v2', 'trust_weight_update',
   'mcp_tool', 'mcp://com.etzhayyim.apps.wellbecoming.trustWeightUpdate',
   '{"input_keys":[],"result_key":"out","args":{"name":"com.etzhayyim.apps.wellbecoming.trustWeightUpdate"}}',
   '2026-05-09T00:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'wellbecoming_belief_influence_propagate.v2' WHERE assistant_id = 'wellbecoming_belief_influence_propagate';
UPDATE vertex_langgraph_assistant SET superseded_by = 'wellbecoming_belief_noise_inject.v2'        WHERE assistant_id = 'wellbecoming_belief_noise_inject';
UPDATE vertex_langgraph_assistant SET superseded_by = 'wellbecoming_belief_restoring_capture.v2'   WHERE assistant_id = 'wellbecoming_belief_restoring_capture';
UPDATE vertex_langgraph_assistant SET superseded_by = 'wellbecoming_detect_bottleneck.v2'          WHERE assistant_id = 'wellbecoming_detect_bottleneck';
UPDATE vertex_langgraph_assistant SET superseded_by = 'wellbecoming_floor_violation_alert.v2'      WHERE assistant_id = 'wellbecoming_floor_violation_alert';
UPDATE vertex_langgraph_assistant SET superseded_by = 'wellbecoming_minimax_sweep.v2'              WHERE assistant_id = 'wellbecoming_minimax_sweep';
UPDATE vertex_langgraph_assistant SET superseded_by = 'wellbecoming_proactive_connect.v2'          WHERE assistant_id = 'wellbecoming_proactive_connect';
UPDATE vertex_langgraph_assistant SET superseded_by = 'wellbecoming_process_mining.v2'             WHERE assistant_id = 'wellbecoming_process_mining';
UPDATE vertex_langgraph_assistant SET superseded_by = 'wellbecoming_trust_weight_update.v2'        WHERE assistant_id = 'wellbecoming_trust_weight_update';

FLUSH;
