-- ADR-2605082000 Phase D2 — sweep remaining live `router` code-islands.
--
-- Each topology config below is re-INSERTed with `field`-based
-- conditional_edges. The upstream node primitives have been extended to
-- emit a routing field (`nextRoute` / `domain` / `kind` / `route`) whose
-- value matches the path_map keys exactly, so the legacy py_primitive
-- gate functions are retired with no behavioural drift.
--
-- Same-PK INSERT semantics: RisingWave overwrites the existing topology
-- row (audit script's two-pass `latestKind` / `fileOrder` resolution
-- ensures only this re-INSERT counts as live for these assistant_ids).
-- The bulk-51 topology rows used `factory_path, spec` column ordering
-- (no `superseded_by` column). The new INSERTs match that shape; the
-- canonical-v2 rows use the post-bulk-51 `kind, superseded_by, config`
-- order (mirrors the rest of the file).

-- ── bulk-51 py_primitive supervisors (top-level state field) ─────────────

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('etzhayyimcojp-company-ops', 1, 0, 'etzhayyimcojp-company-ops', 2, 'topology', NULL,
   '{"state_keys":["task_type","payload","thread_id","requester_did","domain","routing_reason","result","action_items","omega_score","floor_violated","ok","error"],"entry":"supervisor","edges":[{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"supervisor","field":"domain","paths":{"hr":"hr","finance":"finance","legal":"legal","sales":"sales","governance":"governance","personnel":"personnel","unknown":"governance"},"default":"governance"}]}',
   'etzhayyimcojp-company-ops (Phase D2 field-based routing)', '2026-05-09T05:30:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('lawfirm-marketing-ops', 1, 0, 'lawfirm-marketing-ops', 2, 'topology', NULL,
   '{"state_keys":["task_type","brand","audience","topic","payload","schedule_at","requester_did","thread_id","kind","routing_reason","asset_kind","title","body_md","target_url","asset_uris","compliance_check","compliance_notes","compliance_score","summary","ok","error"],"entry":"supervisor","edges":[{"from":"compliance_gate","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"supervisor","field":"kind","paths":{"content":"content","social":"social","outreach":"outreach","platform":"platform","analytics":"analytics","event":"event","unknown":"content"},"default":"content"}]}',
   'lawfirm-marketing-ops (Phase D2 field-based routing)', '2026-05-09T05:30:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('kaisya-member-assistant', 1, 0, 'kaisya-member-assistant', 2, 'topology', NULL,
   '{"state_keys":["user_upn","session_id","user_message","history","channel","member_did","member_name","member_role","raci_summary","route","nextRoute","routing_reason","sub_result","sub_summary","reply_text","citations","requires_human_approval","ok","error"],"entry":"resolve_member","edges":[{"from":"load_context","to":"supervisor"},{"from":"direct_reply","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"resolve_member","field":"nextRoute","paths":{"denied":"direct_reply","load_context":"load_context"},"default":"load_context"},{"from":"supervisor","field":"route","paths":{"company_ops":"company_ops","lawfirm_marketing":"lawfirm_marketing","lawfirm_sales":"lawfirm_sales","direct_reply":"direct_reply","escalate":"direct_reply"},"default":"direct_reply"}]}',
   'kaisya-member-assistant (Phase D2 field-based routing)', '2026-05-09T05:30:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('webmk_create_proposal', 1, 0, 'webmk_create_proposal', 2, 'topology', NULL,
   '{"state_keys":["proposalId","clientName","websiteUrl","industry","targetAudience","budgetJpy","deliveryEmail","createAdCampaign","company_context","competitor_summary","strategy_json","copy_markdown","quality_score","retry_count","nextRoute","ok","error"],"entry":"research_company","edges":[{"from":"research_company","to":"analyze_competitors"},{"from":"analyze_competitors","to":"generate_strategy"},{"from":"generate_strategy","to":"generate_copy"},{"from":"generate_copy","to":"quality_gate"},{"from":"store_proposal","to":"END"}],"conditional_edges":[{"from":"quality_gate","field":"nextRoute","paths":{"store":"store_proposal","retry":"generate_strategy"},"default":"store"}]}',
   'webmk_create_proposal (Phase D2 field-based routing)', '2026-05-09T05:30:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, factory_path, spec, description, created_at)
VALUES
  ('animeka_autopilot', 1, 0, 'animeka_autopilot', 2, 'topology', NULL,
   '{"state_keys":["cutId","sceneText","visualPrompt","sbCid","lyCid","kfCid","bgCid","bgPrompt","layoutBgMood","postStatus","nextRoute","ok","error"],"entry":"generate_scene_text","edges":[{"from":"generate_scene_text","to":"generate_storyboard"},{"from":"generate_storyboard_retry","to":"generate_layout"},{"from":"generate_layout","to":"generate_keyframe"},{"from":"generate_keyframe","to":"generate_background"},{"from":"generate_background","to":"compose_post"},{"from":"compose_post","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"generate_storyboard","field":"nextRoute","paths":{"generate_storyboard_retry":"generate_storyboard_retry","generate_layout":"generate_layout"},"default":"generate_layout"}]}',
   'animeka_autopilot (Phase D2 field-based routing)', '2026-05-09T05:30:00Z');

-- ── canonical v2 mcp_tool topologies (envelope: <resultKey>.result.<field>) ─

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES
  ('koke.cycle.v2', 1, 0, 'koke.cycle.v2', 3, 'topology', NULL,
   '{"state_keys":["scanOut","fixOut","classifyOut","hakkouOut","saikinOut","ok","error"],"entry":"scan","edges":[{"from":"fix","to":"classify"},{"from":"handoff_hakkou","to":"END"},{"from":"handoff_saikin","to":"END"}],"conditional_edges":[{"from":"scan","field":"scanOut.result.nextRoute","paths":{"fix":"fix","no_signals":"END"},"default":"no_signals"},{"from":"classify","field":"classifyOut.result.nextRoute","paths":{"hakkou":"handoff_hakkou","saikin":"handoff_saikin"},"default":"saikin"}]}',
   'koke primary-fixation cycle (canonical v2, Phase D2 field-based routing)',
   '2026-05-09T05:30:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES
  ('wellbecoming_floor_violation_alert.v2', 1, 0, 'wellbecoming_floor_violation_alert.v2', 3, 'topology', NULL,
   '{"state_keys":["window_minutes","floor_violation_count","violation_ids","has_violations","alert_emitted","ok","error"],"entry":"floor_check","edges":[{"from":"floor_alert","to":"END"}],"conditional_edges":[{"from":"floor_check","field":"floor_violation_count.result.nextRoute","paths":{"floor_alert":"floor_alert","__end__":"END"},"default":"__end__"}]}',
   'wellbecoming floor-violation alert (canonical v2, Phase D2 field-based routing)',
   '2026-05-09T05:30:00Z');

INSERT INTO vertex_langgraph_assistant
  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at)
VALUES
  ('shinshi_seed_gap_fill.v2', 1, 0, 'shinshi_seed_gap_fill.v2', 3, 'topology', NULL,
   '{"state_keys":["findOut","seedOut","auditOut","ok","error"],"entry":"find_incomplete","edges":[{"from":"bulk_seed","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"find_incomplete","field":"findOut.result.nextRoute","paths":{"bulk_seed":"bulk_seed","emit_audit":"emit_audit"},"default":"emit_audit"}]}',
   'shinshi seed-gap-fill (canonical v2, Phase D2 field-based routing)',
   '2026-05-09T05:30:00Z');

FLUSH;
