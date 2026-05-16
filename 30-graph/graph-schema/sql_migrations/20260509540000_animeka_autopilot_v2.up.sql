-- ADR-2605082000 Phase E3 — animeka_autopilot decomposition.
--
-- Target: animeka_autopilot (8 live py_primitive nodes from bulk-51).
-- Pattern: scene-text LLM → 5 ComfyUI binding nodes → social post → audit.
--
-- Decomposition outcome:
--   generate_scene_text         mcp_tool      RETIRED → llm.chat (user_template)
--   generate_storyboard         py_primitive  KEPT (ComfyUI binary image
--                                                   generation = ADR §Known
--                                                   constraints #4 native
--                                                   side-effect exception).
--                                                   Sets nextRoute (Phase D2).
--   generate_storyboard_retry   py_primitive  KEPT (ComfyUI exception)
--   generate_layout             py_primitive  KEPT (ComfyUI exception)
--   generate_keyframe           py_primitive  KEPT (ComfyUI exception)
--   generate_background         py_primitive  KEPT (ComfyUI exception)
--   compose_post                py_primitive  KEPT (PDS dispatch + image
--                                                   embed = native side-effect)
--   emit_audit                  mcp_tool      RETIRED → ai.gftd.tools.audit.emit
--
-- Net: 8 py_primitive → 2 mcp_tool + 6 py_primitive. -2 live py_primitive.
--
-- Routing: generate_storyboard's field-based conditional edge (Phase D2,
-- field=nextRoute) is preserved unchanged in the v2 config.
--
-- Note: ComfyUI nodes that previously read state.sceneText now read via
-- _envelope_content(state, "sceneTextLlmOut", "sceneText") to handle the
-- mcp_tool envelope shape from the upstream llm.chat node.

INSERT INTO vertex_langgraph_assistant (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at) VALUES ('animeka_autopilot.v2', 0, 0, 'animeka_autopilot.v2', 2, 'topology', NULL, '{"state_keys":["cutId","sceneText","sceneTextLlmOut","visualPrompt","sbCid","lyCid","kfCid","bgCid","bgPrompt","layoutBgMood","postStatus","nextRoute","emitAuditOut","ok","error"],"entry":"generate_scene_text","edges":[{"from":"generate_scene_text","to":"generate_storyboard"},{"from":"generate_storyboard_retry","to":"generate_layout"},{"from":"generate_layout","to":"generate_keyframe"},{"from":"generate_keyframe","to":"generate_background"},{"from":"generate_background","to":"compose_post"},{"from":"compose_post","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"generate_storyboard","field":"nextRoute","paths":{"generate_storyboard_retry":"generate_storyboard_retry","generate_layout":"generate_layout"},"default":"generate_layout"}]}', 'animeka_autopilot (Phase E3: scene-text LLM + audit emit mcp_tool, 5 ComfyUI + compose_post py_primitive exception)', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('animeka_autopilot.v2:generate_scene_text', 0, 0, 'animeka_autopilot.v2', 'generate_scene_text', 'mcp_tool', 'mcp://ai.gftd.tools.llm.chat', '{"result_key":"sceneTextLlmOut","args":{"name":"ai.gftd.tools.llm.chat","tier":"deep","system":"You are an anime scene writer. Write SHORT (1-3 sentence) evocative scene descriptions for an anime short starring Misaki — a thoughtful high-school girl in a navy blazer with long dark hair. Vary the mood: calm mornings, wistful afternoons, introspective evenings. Output only the scene description, no preamble.","user_template":"Generate a fresh scene now.","maxTokens":400,"temperature":0.85}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('animeka_autopilot.v2:generate_storyboard', 0, 0, 'animeka_autopilot.v2', 'generate_storyboard', 'py_primitive', 'pymagatama.langgraph_graphs.animeka_autopilot:generate_storyboard', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('animeka_autopilot.v2:generate_storyboard_retry', 0, 0, 'animeka_autopilot.v2', 'generate_storyboard_retry', 'py_primitive', 'pymagatama.langgraph_graphs.animeka_autopilot:generate_storyboard_retry', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('animeka_autopilot.v2:generate_layout', 0, 0, 'animeka_autopilot.v2', 'generate_layout', 'py_primitive', 'pymagatama.langgraph_graphs.animeka_autopilot:generate_layout', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('animeka_autopilot.v2:generate_keyframe', 0, 0, 'animeka_autopilot.v2', 'generate_keyframe', 'py_primitive', 'pymagatama.langgraph_graphs.animeka_autopilot:generate_keyframe', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('animeka_autopilot.v2:generate_background', 0, 0, 'animeka_autopilot.v2', 'generate_background', 'py_primitive', 'pymagatama.langgraph_graphs.animeka_autopilot:generate_background', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('animeka_autopilot.v2:compose_post', 0, 0, 'animeka_autopilot.v2', 'compose_post', 'py_primitive', 'pymagatama.langgraph_graphs.animeka_autopilot:compose_post', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('animeka_autopilot.v2:emit_audit', 0, 0, 'animeka_autopilot.v2', 'emit_audit', 'mcp_tool', 'mcp://ai.gftd.tools.audit.emit', '{"input_paths":{"cutId":"cutId","sbCid":"sbCid","lyCid":"lyCid","kfCid":"kfCid","bgCid":"bgCid","postStatus":"postStatus","ok":"ok"},"result_key":"emitAuditOut","args":{"name":"ai.gftd.tools.audit.emit","actor":"did:web:animeka.gftd.ai","action":"animeka.autopilot"}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_deployment (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at) VALUES ('langgraph.builtin.animeka_autopilot.v2', 0, 0, 'langgraph.builtin.animeka_autopilot.v2', 'animeka_autopilot.v2', 2, 'active', 1, '2026-05-09T09:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'animeka_autopilot.v2'
 WHERE assistant_id = 'animeka_autopilot';

FLUSH;
