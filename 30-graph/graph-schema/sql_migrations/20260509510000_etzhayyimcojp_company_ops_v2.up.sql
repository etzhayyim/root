-- ADR-2605082000 Phase E3 — etzhayyimcojp_company_ops decomposition.
--
-- Target: etzhayyimcojp-company-ops (8 live py_primitive nodes from bulk-51:
-- supervisor + hr + finance + legal + sales + governance + personnel +
-- emit_audit).
--
-- Decomposition outcome (v2, 16 nodes):
--   supervisor              py_primitive  KEPT (prefix-match + LLM fallback
--                                          producing state.domain for Phase D2
--                                          field routing — ADR §Known
--                                          constraints exception)
--   legal_fetch_ctx         py_primitive  KEPT (pre-LLM SQL: active legal
--                                          cases → state.legalContext)
--   governance_fetch_ctx    py_primitive  KEPT (pre-LLM SQL: latest org
--                                          snapshot → state.governanceContext)
--   personnel_fetch_ctx     py_primitive  KEPT (pre-LLM SQL: active personnel
--                                          → state.personnelContext)
--   <domain>_call_llm × 6   mcp_tool      RETIRED → mcp://com.etzhayyim.tools.llm.chat
--                                          (user_template + input_paths feed
--                                          state slices as template vars)
--   <domain>_persist × 6    py_primitive  KEPT (parse LLM JSON envelope, run
--                                          db_writes loop, emit audit_record;
--                                          governance_persist also writes the
--                                          dedicated governance_event row +
--                                          omega_score / floor_violated)
--   emit_audit              mcp_tool      RETIRED → mcp://com.etzhayyim.tools.audit.emit
--                                          (consumes state.audit_record set by
--                                          each persist node)
--
-- Net: 8 py_primitive (v1) → 10 py_primitive + 7 mcp_tool (v2). Live
-- py_primitive delta vs v1: +2 (supervisor 1 + 3 ctx fetches + 6 persists =
-- 10 vs v1's 8). Live mcp_tool delta: +7. The v1 row is marked superseded.
--
-- Field-based routing preserved (ADR Phase D2): supervisor's field=`domain`
-- still routes 7 paths (hr/finance/legal/sales/governance/personnel/unknown).
-- legal/governance/personnel route to *_fetch_ctx first, others go straight
-- to *_call_llm.

INSERT INTO vertex_langgraph_assistant (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind, superseded_by, config, description, created_at) VALUES ('etzhayyimcojp-company-ops.v2', 0, 0, 'etzhayyimcojp-company-ops.v2', 2, 'topology', NULL, '{"state_keys":["task_type","payload","thread_id","requester_did","domain","routing_reason","legalContext","governanceContext","personnelContext","hrLlmOut","financeLlmOut","legalLlmOut","salesLlmOut","governanceLlmOut","personnelLlmOut","result","action_items","omega_score","floor_violated","hr_audit_record","finance_audit_record","legal_audit_record","sales_audit_record","governance_audit_record","personnel_audit_record","audit_record","auditOut","ok","error"],"entry":"supervisor","edges":[{"from":"legal_fetch_ctx","to":"legal_call_llm"},{"from":"governance_fetch_ctx","to":"governance_call_llm"},{"from":"personnel_fetch_ctx","to":"personnel_call_llm"},{"from":"hr_call_llm","to":"hr_persist"},{"from":"finance_call_llm","to":"finance_persist"},{"from":"legal_call_llm","to":"legal_persist"},{"from":"sales_call_llm","to":"sales_persist"},{"from":"governance_call_llm","to":"governance_persist"},{"from":"personnel_call_llm","to":"personnel_persist"},{"from":"hr_persist","to":"emit_audit"},{"from":"finance_persist","to":"emit_audit"},{"from":"legal_persist","to":"emit_audit"},{"from":"sales_persist","to":"emit_audit"},{"from":"governance_persist","to":"emit_audit"},{"from":"personnel_persist","to":"emit_audit"},{"from":"emit_audit","to":"END"}],"conditional_edges":[{"from":"supervisor","field":"domain","paths":{"hr":"hr_call_llm","finance":"finance_call_llm","legal":"legal_fetch_ctx","sales":"sales_call_llm","governance":"governance_fetch_ctx","personnel":"personnel_fetch_ctx","unknown":"governance_fetch_ctx"},"default":"governance_fetch_ctx"}]}', 'etzhayyimcojp-company-ops (Phase E3: supervisor + 3 fetch_ctx + 6 persist py_primitive + 6 LLM mcp_tool + emit_audit mcp_tool)', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:supervisor', 0, 0, 'etzhayyimcojp-company-ops.v2', 'supervisor', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:supervisor', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:legal_fetch_ctx', 0, 0, 'etzhayyimcojp-company-ops.v2', 'legal_fetch_ctx', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:legal_fetch_ctx', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:governance_fetch_ctx', 0, 0, 'etzhayyimcojp-company-ops.v2', 'governance_fetch_ctx', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:governance_fetch_ctx', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:personnel_fetch_ctx', 0, 0, 'etzhayyimcojp-company-ops.v2', 'personnel_fetch_ctx', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:personnel_fetch_ctx', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:hr_call_llm', 0, 0, 'etzhayyimcojp-company-ops.v2', 'hr_call_llm', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"task_type":"task_type","payload":"payload"},"result_key":"hrLlmOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"structured","system":"You are the HR AI agent for Etzhayyim Japan株式会社 (principal: amanomibashira).\nHandle: onboarding, offboarding, attendance records, payroll calculation,\nsocial insurance procedures, performance reviews, hiring decisions.\n\nOutput JSON: {action, summary (Japanese), db_writes:[{table,row}], action_items:[], ok:true}","user_template":"task: {task_type}\ndata: {payload}","maxTokens":1000,"temperature":0.3}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:finance_call_llm', 0, 0, 'etzhayyimcojp-company-ops.v2', 'finance_call_llm', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"task_type":"task_type","payload":"payload"},"result_key":"financeLlmOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"structured","system":"You are the Finance/Accounting AI agent for Etzhayyim Japan株式会社 (principal: amanomibashira).\nHandle: journal entries (仕訳), invoices (請求書), expense approval (経費承認),\ntax filings, cash flow forecasts, accounts payable/receivable.\n\nOutput JSON: {action, journal_entry:{debit,credit,amount_jpy,description}, summary (Japanese), db_writes:[{table,row}], action_items:[], ok:true}","user_template":"task: {task_type}\ndata: {payload}","maxTokens":1200,"temperature":0.3}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:legal_call_llm', 0, 0, 'etzhayyimcojp-company-ops.v2', 'legal_call_llm', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"task_type":"task_type","payload":"payload","legalContext":"legalContext"},"result_key":"legalLlmOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"structured","system":"You are the Legal/Compliance AI agent (CLO support) for Etzhayyim Japan株式会社.\nPrincipal: amanomibashira. Active cases in kaisya.etzhayyim.com: LingLing著作権 / 鈴木損害賠償 / 鹿児島大学技術移転 / 松岡NDA.\n\nHandle: contract review, litigation status, compliance checks, IP procedures, corporate filings, regulatory inquiries.\n\nOutput JSON: {action, risk_level:low|medium|high|critical, summary (Japanese), case_updates:[{case_id,update}], db_writes:[{table,row}], action_items:[], ok:true}","user_template":"task: {task_type}\ndata: {payload}\n{legalContext}","maxTokens":1200,"temperature":0.3}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:sales_call_llm', 0, 0, 'etzhayyimcojp-company-ops.v2', 'sales_call_llm', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"task_type":"task_type","payload":"payload"},"result_key":"salesLlmOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"structured","system":"You are the Sales/BD AI agent for Etzhayyim Japan株式会社 (principal: amanomibashira).\nHandle: CRM records, proposal generation (提案書), order management (受注), BD pipeline tracking, customer relationship notes.\n\nOutput JSON: {action, pipeline_update:{customer,stage,amount_jpy}, summary (Japanese), db_writes:[{table,row}], action_items:[], ok:true}","user_template":"task: {task_type}\ndata: {payload}","maxTokens":1000,"temperature":0.3}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:governance_call_llm', 0, 0, 'etzhayyimcojp-company-ops.v2', 'governance_call_llm', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"task_type":"task_type","payload":"payload","governanceContext":"governanceContext"},"result_key":"governanceLlmOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"structured","system":"You are the Governance AI agent for etzhayyimcojp.etzhayyim.com (amanomibashira principal).\nEvaluate Ω(t) = Shannon_η(t) × U_total(t) and generate management decisions.\n\nΩ axes:\n  Spirit       = OKR attainment + CEO strategic clarity + Shannon η\n  Wellbecoming = delivery quality + team growth + project completion rate\n  Feeling      = team morale (inverse of pending task pressure) + legal load\n  Buffer       = financial runway (months) + infra health [0-1]\n\nFloor rule: any axis = 0 → U_total = 0 (Spirit zero kills utility).\n\nOutput JSON: {omega_score, floor_violated, axis_scores:{spirit,wellbecoming,feeling,buffer}, decisions:[{priority,decision,assignee_did}], summary (Japanese), action_items:[], ok:true}","user_template":"task: {task_type}\ndata: {payload}\n{governanceContext}","maxTokens":1500,"temperature":0.3}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:personnel_call_llm', 0, 0, 'etzhayyimcojp-company-ops.v2', 'personnel_call_llm', 'mcp_tool', 'mcp://com.etzhayyim.tools.llm.chat', '{"input_paths":{"task_type":"task_type","payload":"payload","personnelContext":"personnelContext"},"result_key":"personnelLlmOut","args":{"name":"com.etzhayyim.tools.llm.chat","tier":"structured","system":"You are the Personnel/HR-Ops AI agent for Etzhayyim Japan株式会社 (principal: amanomibashira).\nManage contracted person records, role definitions, project assignments, RACI matrices.\n\nTables: vertex_etzhayyimcojp_person / vertex_etzhayyimcojp_role / vertex_etzhayyimcojp_assignment / vertex_etzhayyimcojp_raci / vertex_etzhayyimcojp_okr.\n\nTasks: personnel.{list,get,update} / role.{list,assign} / assignment.{create,end,list} / raci.{assign,list,lookup}.\n\nOutput JSON: {action, summary (Japanese), queries:[{sql,params}], db_writes:[{table,row}], action_items:[], ok:true}","user_template":"task: {task_type}\ndata: {payload}\n{personnelContext}","maxTokens":1200,"temperature":0.3}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:hr_persist', 0, 0, 'etzhayyimcojp-company-ops.v2', 'hr_persist', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:hr_persist', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:finance_persist', 0, 0, 'etzhayyimcojp-company-ops.v2', 'finance_persist', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:finance_persist', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:legal_persist', 0, 0, 'etzhayyimcojp-company-ops.v2', 'legal_persist', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:legal_persist', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:sales_persist', 0, 0, 'etzhayyimcojp-company-ops.v2', 'sales_persist', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:sales_persist', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:governance_persist', 0, 0, 'etzhayyimcojp-company-ops.v2', 'governance_persist', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:governance_persist', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:personnel_persist', 0, 0, 'etzhayyimcojp-company-ops.v2', 'personnel_persist', 'py_primitive', 'pymagatama.langgraph_graphs.etzhayyimcojp_company_ops:personnel_persist', NULL, '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_assistant_node (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at) VALUES ('etzhayyimcojp-company-ops.v2:emit_audit', 0, 0, 'etzhayyimcojp-company-ops.v2', 'emit_audit', 'mcp_tool', 'mcp://com.etzhayyim.tools.audit.emit', '{"input_paths":{"recordJson":"audit_record"},"result_key":"auditOut","args":{"name":"com.etzhayyim.tools.audit.emit","repo":"did:web:etzhayyimcojp.etzhayyim.com","collection":"com.etzhayyim.apps.etzhayyimcojp.ops","action":"create"}}', '2026-05-09T09:00:00Z');

INSERT INTO vertex_langgraph_deployment (vertex_id, _seq, sensitivity_ord, nsid, assistant_id, version, status, replicas, updated_at) VALUES ('langgraph.builtin.etzhayyimcojp-company-ops.v2', 0, 0, 'langgraph.builtin.etzhayyimcojp-company-ops.v2', 'etzhayyimcojp-company-ops.v2', 2, 'active', 1, '2026-05-09T09:00:00Z');

UPDATE vertex_langgraph_assistant SET superseded_by = 'etzhayyimcojp-company-ops.v2'
 WHERE assistant_id = 'etzhayyimcojp-company-ops';

FLUSH;
