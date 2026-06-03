DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyimcojp_omega_daily;

DELETE FROM vertex_bpmn_lexicon_binding WHERE process_id LIKE 'etzhayyimcojp%';

DELETE FROM vertex_bpmn_process_def WHERE process_id LIKE 'etzhayyimcojp%';

DROP TABLE IF EXISTS vertex_etzhayyimcojp_governance_event;

DROP TABLE IF EXISTS vertex_etzhayyimcojp_sales_event;

DROP TABLE IF EXISTS vertex_etzhayyimcojp_legal_event;

DROP TABLE IF EXISTS vertex_etzhayyimcojp_finance_event;

DROP TABLE IF EXISTS vertex_etzhayyimcojp_hr_event;
