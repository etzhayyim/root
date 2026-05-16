DROP MATERIALIZED VIEW IF EXISTS mv_gftdcojp_omega_daily;

DELETE FROM vertex_bpmn_lexicon_binding WHERE process_id LIKE 'gftdcojp%';

DELETE FROM vertex_bpmn_process_def WHERE process_id LIKE 'gftdcojp%';

DROP TABLE IF EXISTS vertex_gftdcojp_governance_event;

DROP TABLE IF EXISTS vertex_gftdcojp_sales_event;

DROP TABLE IF EXISTS vertex_gftdcojp_legal_event;

DROP TABLE IF EXISTS vertex_gftdcojp_finance_event;

DROP TABLE IF EXISTS vertex_gftdcojp_hr_event;
