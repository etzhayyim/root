DELETE FROM vertex_bpmn_lexicon_binding WHERE process_id LIKE 'etzhayyimcojp_personnel%';

DELETE FROM vertex_bpmn_process_def WHERE process_id LIKE 'etzhayyimcojp_personnel%';

DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyimcojp_raci_by_task;

DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyimcojp_active_assignments;

DROP TABLE IF EXISTS vertex_etzhayyimcojp_okr;

DROP TABLE IF EXISTS vertex_etzhayyimcojp_raci;

DROP TABLE IF EXISTS vertex_etzhayyimcojp_assignment;

DROP TABLE IF EXISTS vertex_etzhayyimcojp_role;

DROP TABLE IF EXISTS vertex_etzhayyimcojp_person;
