CREATE TABLE IF NOT EXISTS vertex_etzhayyimcojp_hr_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      action varchar,
      summary varchar,
      employee_did varchar,
      department varchar,
      status varchar DEFAULT 'open',
      action_items_json varchar,
      llm_model varchar,
      created_at varchar,
      sensitivity_ord int DEFAULT 200,
      owner_did varchar);

CREATE TABLE IF NOT EXISTS vertex_etzhayyimcojp_finance_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      action varchar,
      journal_debit varchar,
      journal_credit varchar,
      amount_jpy double precision,
      description varchar,
      summary varchar,
      status varchar DEFAULT 'open',
      action_items_json varchar,
      llm_model varchar,
      created_at varchar,
      sensitivity_ord int DEFAULT 200,
      owner_did varchar);

CREATE TABLE IF NOT EXISTS vertex_etzhayyimcojp_legal_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      action varchar,
      risk_level varchar DEFAULT 'low',
      summary varchar,
      case_id varchar,
      status varchar DEFAULT 'open',
      action_items_json varchar,
      llm_model varchar,
      created_at varchar,
      sensitivity_ord int DEFAULT 300,
      owner_did varchar);

CREATE TABLE IF NOT EXISTS vertex_etzhayyimcojp_sales_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      action varchar,
      customer_name varchar,
      pipeline_stage varchar,
      amount_jpy double precision,
      summary varchar,
      status varchar DEFAULT 'open',
      action_items_json varchar,
      llm_model varchar,
      created_at varchar,
      sensitivity_ord int DEFAULT 100,
      owner_did varchar);

CREATE TABLE IF NOT EXISTS vertex_etzhayyimcojp_governance_event (
      vertex_id varchar PRIMARY KEY,
      task_type varchar NOT NULL,
      omega_score double precision,
      floor_violated boolean DEFAULT false,
      decisions_json varchar,
      summary varchar,
      status varchar DEFAULT 'open',
      created_at varchar,
      sensitivity_ord int DEFAULT 100,
      owner_did varchar);

INSERT INTO vertex_bpmn_process_def
      (vertex_id, process_id, name, description, version, bpmn_xml, status, created_at)
    VALUES
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/etzhayyimcojp-governance-daily-v1',
        'etzhayyimcojp_governance_daily_check',
        'etzhayyimcojp Governance Daily Check',
        'Daily Ω(t) governance check via LangGraph etzhayyimcojp-company-ops (amanomibashira principal)',
        1,
        '',
        'active',
        now()
      ),
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/etzhayyimcojp-ops-dispatch-v1',
        'etzhayyimcojp_company_ops_dispatch',
        'etzhayyimcojp Company Ops Dispatch',
        'XRPC-triggered domain task dispatch (HR/Finance/Legal/Sales/Governance) via LangGraph',
        1,
        '',
        'active',
        now()
      );

INSERT INTO vertex_bpmn_lexicon_binding
      (vertex_id, process_id, nsid, binding_type, status, created_at)
    VALUES
      (
        'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyimcojp-ops-dispatch-xrpc-v1',
        'etzhayyimcojp_company_ops_dispatch',
        'com.etzhayyim.apps.etzhayyimcojp.companyOpsDispatch',
        'xrpc',
        'active',
        now()
      );

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyimcojp_omega_daily AS
    SELECT
      DATE(created_at::timestamp) AS day,
      AVG(omega_score)            AS avg_omega,
      MIN(omega_score)            AS min_omega,
      MAX(omega_score)            AS max_omega,
      COUNT(*)                    AS check_count,
      BOOL_OR(floor_violated)     AS any_floor_violated
    FROM vertex_etzhayyimcojp_governance_event
    WHERE omega_score IS NOT NULL
    GROUP BY DATE(created_at::timestamp);
