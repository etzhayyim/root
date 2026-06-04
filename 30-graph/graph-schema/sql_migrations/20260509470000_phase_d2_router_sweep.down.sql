-- Rollback Phase D2 router sweep — restore the legacy `router`-based
-- conditional_edges. The router callables still exist in
-- pymagatama.langgraph_graphs.* / pymagatama.primitives.* so the
-- rollback target is functionally identical to the pre-D2 state.

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('etzhayyimcojp-company-ops', 0, 0, 'etzhayyimcojp-company-ops', 1, 'topology', NULL,
   '{"state_keys":["task_type","payload","thread_id","requester_did","domain","routing_reason","result","action_items","omega_score","floor_violated","ok","error"],"entry":"supervisor","edges":[{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"supervisor","router":"pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:_route_domain","paths":{"hr":"hr","finance":"finance","legal":"legal","sales":"sales","governance":"governance","personnel":"personnel","unknown":"governance"}}]}',
   'auto-migrated topology (P3 batch)', '2026-05-08T19:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('lawfirm-marketing-ops', 0, 0, 'lawfirm-marketing-ops', 1, 'topology', NULL,
   '{"state_keys":["task_type","brand","audience","topic","payload","schedule_at","requester_did","thread_id","kind","routing_reason","asset_kind","title","body_md","target_url","asset_uris","compliance_check","compliance_notes","compliance_score","summary","ok","error"],"entry":"supervisor","edges":[{"from":"compliance_gate","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"supervisor","router":"pymagatama.langgraph_graphs.lawfirm_marketing_ops:_route_kind","paths":{"content":"content","social":"social","outreach":"outreach","platform":"platform","analytics":"analytics","event":"event","unknown":"content"}}]}',
   'auto-migrated topology (P3 batch)', '2026-05-08T19:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('kaisya-member-assistant', 0, 0, 'kaisya-member-assistant', 1, 'topology', NULL,
   '{"state_keys":["user_upn","session_id","user_message","history","channel","member_did","member_name","member_role","raci_summary","route","routing_reason","sub_result","sub_summary","reply_text","citations","requires_human_approval","ok","error"],"entry":"resolve_member","edges":[{"from":"load_context","to":"supervisor"},{"from":"direct_reply","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"resolve_member","router":"pymagatama.langgraph_graphs.kaisya_member_assistant:_after_resolve","paths":{"denied":"direct_reply","load_context":"load_context"}},{"from":"supervisor","router":"pymagatama.langgraph_graphs.kaisya_member_assistant:_route_after_supervisor","paths":{"company_ops":"company_ops","lawfirm_marketing":"lawfirm_marketing","lawfirm_sales":"lawfirm_sales","direct_reply":"direct_reply","escalate":"direct_reply"}}]}',
   'auto-migrated topology (P3 batch)', '2026-05-08T19:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('webmk_create_proposal', 0, 0, 'webmk_create_proposal', 1, 'topology', NULL,
   '{"state_keys":["proposalId","clientName","websiteUrl","industry","targetAudience","budgetJpy","deliveryEmail","createAdCampaign","company_context","competitor_summary","strategy_json","copy_markdown","quality_score","retry_count","ok","error"],"entry":"research_company","edges":[{"from":"research_company","to":"analyze_competitors"},{"from":"analyze_competitors","to":"generate_strategy"},{"from":"generate_strategy","to":"generate_copy"},{"from":"generate_copy","to":"quality_gate"},{"from":"store_proposal","to":"END"}],"conditional_edges":[{"from":"quality_gate","router":"pymagatama.langgraph_graphs.webmk_proposal:should_retry","paths":{"store":"store_proposal","retry":"generate_strategy"}}]}',
   'auto-migrated topology (P3 batch)', '2026-05-08T19:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('animeka_autopilot', 0, 0, 'animeka_autopilot', 1, 'topology', NULL,
   '{"state_keys":["cutId","sceneText","visualPrompt","sbCid","lyCid","kfCid","bgCid","bgPrompt","layoutBgMood","postStatus","ok","error"],"entry":"generate_scene_text","edges":[{"from":"generate_scene_text","to":"generate_storyboard"},{"from":"generate_storyboard_retry","to":"generate_layout"},{"from":"generate_layout","to":"generate_keyframe"},{"from":"generate_keyframe","to":"generate_background"},{"from":"generate_background","to":"compose_post"},{"from":"compose_post","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"generate_storyboard","router":"pymagatama.langgraph_graphs.animeka_autopilot:_route_after_storyboard","paths":{"generate_storyboard_retry":"generate_storyboard_retry","generate_layout":"generate_layout"}}]}',
   'auto-migrated topology (P3 batch)', '2026-05-08T19:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES
  ('koke.cycle.v2', 0, 0, 'koke.cycle.v2', 2, 'topology', NULL,
   '{"state_keys":["scanOut","fixOut","classifyOut","hakkouOut","saikinOut","ok","error"],"entry":"scan","edges":[{"from":"fix","to":"classify"},{"from":"handoff_hakkou","to":"END"},{"from":"handoff_saikin","to":"END"}],"conditional_edges":[{"from":"scan","router":"pymagatama.langgraph_graphs.koke_cycle:_has_signals_gate","paths":{"fix":"fix","no_signals":"END"}},{"from":"classify","router":"pymagatama.langgraph_graphs.koke_cycle:_confidence_gate","paths":{"hakkou":"handoff_hakkou","saikin":"handoff_saikin"}}]}',
   'koke primary-fixation cycle (canonical v2, mcp_tool nodes + conditional routers)',
   '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES
  ('wellbecoming_floor_violation_alert.v2', 0, 0, 'wellbecoming_floor_violation_alert.v2', 2, 'topology', NULL,
   '{"state_keys":["window_minutes","floor_violation_count","violation_ids","has_violations","alert_emitted","ok","error"],"entry":"floor_check","edges":[{"from":"floor_alert","to":"END"}],"conditional_edges":[{"from":"floor_check","router":"pymagatama.langgraph_graphs.wellbecoming_floor_violation_alert:_route_after_check","paths":{"floor_alert":"floor_alert","__end__":"END"}}]}',
   'wellbecoming floor-violation alert (canonical v2)',
   '2026-05-09T00:00:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES
  ('shinshi_seed_gap_fill.v2', 0, 0, 'shinshi_seed_gap_fill.v2', 2, 'topology', NULL,
   '{"state_keys":["findOut","seedOut","auditOut","ok","error"],"entry":"find_incomplete","edges":[{"from":"bulk_seed","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"find_incomplete","router":"pymagatama.langgraph_graphs.shinshi_seed_gap_fill:_route_after_find","paths":{"bulk_seed":"bulk_seed","emit_audit":"emit_audit"}}]}',
   'shinshi seed-gap-fill (canonical v2)',
   '2026-05-09T00:00:00Z');

FLUSH;
