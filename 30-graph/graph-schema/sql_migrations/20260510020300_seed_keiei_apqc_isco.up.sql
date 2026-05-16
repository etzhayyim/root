-- Seed APQC PCF L1 + ISCO-08 binding for the 9 keiei C-suite roles.
-- Re-INSERTs into vertex_keiei_role act as upsert (record-log semantics).
-- Inserts into edge_keiei_role_owns_apqc and edge_keiei_role_isco are
-- preceded by DELETE for re-runnability.
--
-- Mappings:
--
-- ISCO-08 (ILO 4-digit unit groups, all skill_level 4 — managerial):
--   1120  Managing Directors and Chief Executives          → CEO, COO
--   1211  Finance Managers                                  → CFO
--   1212  Human Resource Managers                           → CHRO
--   1219  Business Services and Administration Managers nec → CLO
--   1221  Sales and Marketing Managers                      → CMO
--   1222  Advertising and Public Relations Managers         → CDO
--   1330  Information and Communications Technology Service Managers → CTO, CISO
--
-- APQC PCF L1 primary (cohort DIDs from deps.toml [[cohort_actors]]):
--   1.0  Develop Vision and Strategy        cvsn001a → CEO
--   3.0  Market and Sell Products/Services  cmkt003c → CMO, (CDO secondary)
--   5.0  Deliver Production / Service       cops005e → COO
--   7.0  Develop and Manage Human Capital   chrm007g → CHRO
--   8.0  Manage Information Technology      cinf008h → CTO, (CISO primary too)
--   9.0  Manage Financial Resources         cfin009i → CFO
--   11.0 Manage Risk / Compliance / Resiliency  crsk011k → CLO, (CISO secondary)

-- ─────────────────────────────────────────────────────────────────────────
-- 1. Upsert vertex_keiei_role rows with APQC + ISCO columns filled.
-- ─────────────────────────────────────────────────────────────────────────

INSERT INTO vertex_keiei_role
  (vertex_id, _seq, created_date, sensitivity_ord, owner_did, actor_did, org_did,
   role_id, title, title_ja, mode, human_seat_email, human_seat_did,
   autonomous_classes, confirm_classes, escalate_to_emails,
   financial_action_gated, payroll_gated,
   scope, kpis, reports_to_role_id, notes, created_at,
   apqc_pcf_l1_primary, apqc_pcf_l1_set,
   isco_08_unit_group, isco_08_label, isco_08_skill_level)
VALUES
('at://did:web:etz-hayim/ai.gftd.keiei.role/ceo', 1, CURRENT_DATE, 1,
 'did:web:etz-hayim', 'did:web:keiei.gftd.ai', 'did:web:etz-hayim',
 'ceo', 'Chief Executive (chief-of-staff to 河崎)', '最高経営責任者付き参謀',
 'shadow', 'j.kawasaki@gftd.co.jp', 'did:web:keiei.gftd.ai:human:j-kawasaki',
 'C', 'B', 'j.kawasaki@gftd.co.jp', 0, 0,
 'Aggregate signal across all CXO ledgers; draft CEO responses; prepare decision packets; never speak AS 河崎 to external counterparties.',
 'cxo_alignment_score,packet_turnaround_hours,signal_to_noise_ratio',
 NULL, 'Ultimate principal = amanomibashira. AI-CEO is a chief-of-staff aggregator, not a principal.',
 NOW()::varchar,
 '1.0', '1.0,13.0', '1120', 'Managing Directors and Chief Executives', 4),

('at://did:web:etz-hayim/ai.gftd.keiei.role/coo', 2, CURRENT_DATE, 1,
 'did:web:etz-hayim', 'did:web:keiei.gftd.ai', 'did:web:etz-hayim',
 'coo', 'Chief Operating', '最高執行責任者',
 'shadow', 'a.nakamura@gftd.co.jp', 'did:web:keiei.gftd.ai:human:a-nakamura',
 'C', 'B', 'j.kawasaki@gftd.co.jp', 0, 0,
 'Run the operational backbone: vendor accounts, contract execution, weekly KPI dispatch, cross-team SLA tracking.',
 'sla_breach_count,vendor_provisioning_lead_time_days,wkpi_dispatch_on_time_rate',
 'ceo', '', NOW()::varchar,
 '5.0', '4.0,5.0,6.0', '1120', 'Managing Directors and Chief Executives', 4),

('at://did:web:etz-hayim/ai.gftd.keiei.role/clo', 3, CURRENT_DATE, 1,
 'did:web:etz-hayim', 'did:web:keiei.gftd.ai', 'did:web:etz-hayim',
 'clo', 'Chief Legal', '最高法務責任者',
 'shadow', 'k.bakshi@gftd.co.jp', 'did:web:keiei.gftd.ai:human:k-bakshi',
 'C', 'B', 'j.kawasaki@gftd.co.jp', 0, 0,
 'India / cross-border counsel orchestration; contract redline triage; regulatory monitoring (DPDP, BCI, SEBI). Never signs binding instruments.',
 'redline_turnaround_hours,regulatory_alerts_actioned,external_counsel_quote_variance',
 'ceo', '', NOW()::varchar,
 '11.0', '11.0,12.0', '1219', 'Business Services and Administration Managers Not Elsewhere Classified', 4),

('at://did:web:etz-hayim/ai.gftd.keiei.role/cto', 4, CURRENT_DATE, 1,
 'did:web:etz-hayim', 'did:web:keiei.gftd.ai', 'did:web:etz-hayim',
 'cto', 'Chief Technology (vacant seat — primary mode)', '最高技術責任者（不在・AIプライマリ）',
 'primary', NULL, NULL,
 'C', 'B', 'j.kawasaki@gftd.co.jp', 0, 0,
 'Drive ADRs, infra migrations, deploy gates, RisingWave & Cloudflare topology. Owner of Shannon-Optimal 8-Layer adherence. Class B = 24h auto-disclose to CEO.',
 'adr_throughput_per_week,migration_apply_success_rate,deploy_revert_rate,shannon_eta_score',
 'ceo', 'a.oda 契約終了 2026-04-20. Filling the human CTO seat remains the right action; AI-CTO is a stop-gap.',
 NOW()::varchar,
 '8.0', '2.0,8.0,13.0', '1330', 'Information and Communications Technology Service Managers', 4),

('at://did:web:etz-hayim/ai.gftd.keiei.role/cfo', 5, CURRENT_DATE, 1,
 'did:web:etz-hayim', 'did:web:keiei.gftd.ai', 'did:web:etz-hayim',
 'cfo', 'Chief Financial (vacant — financial-action gated)', '最高財務責任者（不在・送金不可）',
 'primary', NULL, NULL,
 'C', 'B', 'j.kawasaki@gftd.co.jp,a.nakamura@gftd.co.jp', 1, 0,
 'Cash-flow modeling, vendor invoice triage, AR aging, monthly P/L draft, runway projection. MUST NOT initiate any spend, charge, wire, payroll run, or sign legal documents — drafts only.',
 'forecast_accuracy_pct,invoice_cycle_time_days,runway_months,close_cycle_days',
 'ceo', 'No autonomous spend ever. Stripe/Wire/DocuSign require human confirm.',
 NOW()::varchar,
 '9.0', '9.0,10.0,11.0', '1211', 'Finance Managers', 4),

('at://did:web:etz-hayim/ai.gftd.keiei.role/cmo', 6, CURRENT_DATE, 1,
 'did:web:etz-hayim', 'did:web:keiei.gftd.ai', 'did:web:etz-hayim',
 'cmo', 'Chief Marketing (vacant)', '最高マーケティング責任者（不在）',
 'primary', NULL, NULL,
 'C', 'B', 'j.kawasaki@gftd.co.jp,a.nakamura@gftd.co.jp', 0, 0,
 'Owned-channel content (lawfirm.gftd.ai/blog, LinkedIn corporate, ja.gftd.ai). Pipeline narrative. Paid media spend is gated — drafts only.',
 'mql_per_week,blog_publish_cadence,linkedin_engagement_rate,owned_to_paid_ratio',
 'coo', 't.ichihara=Branding 事業部 / k.takahashi=Creative — neither holds CMO seat. Branding is sub-discipline of marketing here.',
 NOW()::varchar,
 '3.0', '3.0,6.0,12.0', '1221', 'Sales and Marketing Managers', 4),

('at://did:web:etz-hayim/ai.gftd.keiei.role/chro', 7, CURRENT_DATE, 1,
 'did:web:etz-hayim', 'did:web:keiei.gftd.ai', 'did:web:etz-hayim',
 'chro', 'Chief Human Resources (vacant — payroll gated)', '最高人事責任者（不在・人事決定不可）',
 'primary', NULL, NULL,
 'C', 'B', 'j.kawasaki@gftd.co.jp,a.nakamura@gftd.co.jp', 0, 1,
 'Internal comms cadence, schedule orchestration (Teams / M365), onboarding doc maintenance, OKR roll-up. Hiring/firing/comp changes are gated — drafts only.',
 'onboarding_completion_pct,1on1_cadence_compliance,internal_response_sla',
 'coo', 'No autonomous hiring/firing/comp changes ever.',
 NOW()::varchar,
 '7.0', '7.0', '1212', 'Human Resource Managers', 4),

('at://did:web:etz-hayim/ai.gftd.keiei.role/ciso', 8, CURRENT_DATE, 1,
 'did:web:etz-hayim', 'did:web:keiei.gftd.ai', 'did:web:etz-hayim',
 'ciso', 'Chief Information Security', '最高情報セキュリティ責任者',
 'shadow', 'n.takahashi@gftd.works', 'did:web:keiei.gftd.ai:human:n-takahashi',
 'C', 'B', 'j.kawasaki@gftd.co.jp,n.takahashi@gftd.works', 0, 0,
 'Vault zero-knowledge invariant enforcement, PII Tier-3 monitoring, key rotation cadence, incident triage. Disclosure decisions human-gated.',
 'rotation_compliance_pct,tier3_leak_findings,incident_mttr_minutes',
 'ceo', '', NOW()::varchar,
 '8.0', '8.0,11.0', '1330', 'Information and Communications Technology Service Managers', 4),

('at://did:web:etz-hayim/ai.gftd.keiei.role/cdo', 9, CURRENT_DATE, 1,
 'did:web:etz-hayim', 'did:web:keiei.gftd.ai', 'did:web:etz-hayim',
 'cdo', 'Chief Design (creative direction)', '最高デザイン責任者',
 'shadow', 'k.takahashi@gftd.co.jp', 'did:web:keiei.gftd.ai:human:k-takahashi',
 'C', 'B', 'k.takahashi@gftd.co.jp,j.kawasaki@gftd.co.jp', 0, 0,
 'Yoro / lawfirm / ja.gftd.ai visual system stewardship; brand asset library; copy tone consistency across touch-points.',
 'brand_consistency_score,asset_library_freshness_days,visual_review_turnaround_hours',
 'cmo', '', NOW()::varchar,
 '3.0', '3.0', '1222', 'Advertising and Public Relations Managers', 4);

-- ─────────────────────────────────────────────────────────────────────────
-- 2. edge_keiei_role_owns_apqc — many-to-many role × APQC PCF L1.
--    primary edge first, then participates/consults edges.
-- ─────────────────────────────────────────────────────────────────────────

DELETE FROM edge_keiei_role_owns_apqc WHERE owner_did = 'did:web:etz-hayim';

-- (role_id, apqc_l1, cohort_did, ownership_kind)
INSERT INTO edge_keiei_role_owns_apqc
  (edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord, owner_did,
   apqc_pcf_l1, ownership_kind, binding_strength)
VALUES
-- CEO primary 1.0 + participates 13.0
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/ceo-1.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/ceo', 'did:plc:pending-cvsn001a', 1, CURRENT_DATE, 1, 'did:web:etz-hayim', '1.0',  'primary',      1.0),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/ceo-13.0', 'at://did:web:etz-hayim/ai.gftd.keiei.role/ceo', 'did:plc:pending-cbiz013m', 2, CURRENT_DATE, 1, 'did:web:etz-hayim', '13.0', 'participates', 0.5),
-- COO primary 5.0 + participates 4.0, 6.0
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/coo-5.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/coo', 'did:plc:pending-cops005e', 3, CURRENT_DATE, 1, 'did:web:etz-hayim', '5.0',  'primary',      1.0),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/coo-4.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/coo', 'did:plc:pending-csup004d', 4, CURRENT_DATE, 1, 'did:web:etz-hayim', '4.0',  'participates', 0.7),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/coo-6.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/coo', 'did:plc:pending-ccsv006f', 5, CURRENT_DATE, 1, 'did:web:etz-hayim', '6.0',  'participates', 0.5),
-- CLO primary 11.0 + participates 12.0
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/clo-11.0', 'at://did:web:etz-hayim/ai.gftd.keiei.role/clo', 'did:plc:pending-crsk011k', 6, CURRENT_DATE, 1, 'did:web:etz-hayim', '11.0', 'primary',      1.0),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/clo-12.0', 'at://did:web:etz-hayim/ai.gftd.keiei.role/clo', 'did:plc:pending-cext012l', 7, CURRENT_DATE, 1, 'did:web:etz-hayim', '12.0', 'participates', 0.5),
-- CTO primary 8.0 + participates 2.0, 13.0
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cto-8.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cto', 'did:plc:pending-cinf008h', 8, CURRENT_DATE, 1, 'did:web:etz-hayim', '8.0',  'primary',      1.0),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cto-2.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cto', 'did:plc:pending-cprd002b', 9, CURRENT_DATE, 1, 'did:web:etz-hayim', '2.0',  'participates', 0.7),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cto-13.0', 'at://did:web:etz-hayim/ai.gftd.keiei.role/cto', 'did:plc:pending-cbiz013m',10, CURRENT_DATE, 1, 'did:web:etz-hayim', '13.0', 'consults',     0.4),
-- CFO primary 9.0 + participates 10.0, 11.0
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cfo-9.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cfo', 'did:plc:pending-cfin009i',11, CURRENT_DATE, 1, 'did:web:etz-hayim', '9.0',  'primary',      1.0),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cfo-10.0', 'at://did:web:etz-hayim/ai.gftd.keiei.role/cfo', 'did:plc:pending-cast010j',12, CURRENT_DATE, 1, 'did:web:etz-hayim', '10.0', 'participates', 0.5),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cfo-11.0', 'at://did:web:etz-hayim/ai.gftd.keiei.role/cfo', 'did:plc:pending-crsk011k',13, CURRENT_DATE, 1, 'did:web:etz-hayim', '11.0', 'consults',     0.5),
-- CMO primary 3.0 + participates 6.0, 12.0
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cmo-3.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cmo', 'did:plc:pending-cmkt003c',14, CURRENT_DATE, 1, 'did:web:etz-hayim', '3.0',  'primary',      1.0),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cmo-6.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cmo', 'did:plc:pending-ccsv006f',15, CURRENT_DATE, 1, 'did:web:etz-hayim', '6.0',  'participates', 0.5),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cmo-12.0', 'at://did:web:etz-hayim/ai.gftd.keiei.role/cmo', 'did:plc:pending-cext012l',16, CURRENT_DATE, 1, 'did:web:etz-hayim', '12.0', 'participates', 0.5),
-- CHRO primary 7.0
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/chro-7.0', 'at://did:web:etz-hayim/ai.gftd.keiei.role/chro','did:plc:pending-chrm007g',17, CURRENT_DATE, 1, 'did:web:etz-hayim', '7.0',  'primary',      1.0),
-- CISO primary 8.0 + participates 11.0
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/ciso-8.0', 'at://did:web:etz-hayim/ai.gftd.keiei.role/ciso','did:plc:pending-cinf008h',18, CURRENT_DATE, 1, 'did:web:etz-hayim', '8.0',  'primary',      1.0),
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/ciso-11.0','at://did:web:etz-hayim/ai.gftd.keiei.role/ciso','did:plc:pending-crsk011k',19, CURRENT_DATE, 1, 'did:web:etz-hayim', '11.0', 'participates', 0.7),
-- CDO primary 3.0
('at://did:web:etz-hayim/ai.gftd.keiei.ownsApqc/cdo-3.0',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cdo', 'did:plc:pending-cmkt003c',20, CURRENT_DATE, 1, 'did:web:etz-hayim', '3.0',  'participates', 0.7);

-- ─────────────────────────────────────────────────────────────────────────
-- 3. edge_keiei_role_isco — role → vertex_occupation (ISCO-08).
--    dst_vid format follows existing isco.gftd.ai actor convention; the
--    canonical row in `vertex_occupation` carries `rkey = isco_08_unit_group`.
-- ─────────────────────────────────────────────────────────────────────────

DELETE FROM edge_keiei_role_isco WHERE owner_did = 'did:web:etz-hayim';

INSERT INTO edge_keiei_role_isco
  (edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord, owner_did, isco_08_unit_group)
VALUES
('at://did:web:etz-hayim/ai.gftd.keiei.iscoOf/ceo',  'at://did:web:etz-hayim/ai.gftd.keiei.role/ceo',  'at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/1120', 1, CURRENT_DATE, 1, 'did:web:etz-hayim', '1120'),
('at://did:web:etz-hayim/ai.gftd.keiei.iscoOf/coo',  'at://did:web:etz-hayim/ai.gftd.keiei.role/coo',  'at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/1120', 2, CURRENT_DATE, 1, 'did:web:etz-hayim', '1120'),
('at://did:web:etz-hayim/ai.gftd.keiei.iscoOf/clo',  'at://did:web:etz-hayim/ai.gftd.keiei.role/clo',  'at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/1219', 3, CURRENT_DATE, 1, 'did:web:etz-hayim', '1219'),
('at://did:web:etz-hayim/ai.gftd.keiei.iscoOf/cto',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cto',  'at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/1330', 4, CURRENT_DATE, 1, 'did:web:etz-hayim', '1330'),
('at://did:web:etz-hayim/ai.gftd.keiei.iscoOf/cfo',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cfo',  'at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/1211', 5, CURRENT_DATE, 1, 'did:web:etz-hayim', '1211'),
('at://did:web:etz-hayim/ai.gftd.keiei.iscoOf/cmo',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cmo',  'at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/1221', 6, CURRENT_DATE, 1, 'did:web:etz-hayim', '1221'),
('at://did:web:etz-hayim/ai.gftd.keiei.iscoOf/chro', 'at://did:web:etz-hayim/ai.gftd.keiei.role/chro', 'at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/1212', 7, CURRENT_DATE, 1, 'did:web:etz-hayim', '1212'),
('at://did:web:etz-hayim/ai.gftd.keiei.iscoOf/ciso', 'at://did:web:etz-hayim/ai.gftd.keiei.role/ciso', 'at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/1330', 8, CURRENT_DATE, 1, 'did:web:etz-hayim', '1330'),
('at://did:web:etz-hayim/ai.gftd.keiei.iscoOf/cdo',  'at://did:web:etz-hayim/ai.gftd.keiei.role/cdo',  'at://did:web:isco.gftd.ai/ai.gftd.isco.occupation/1222', 9, CURRENT_DATE, 1, 'did:web:etz-hayim', '1222');

FLUSH;
