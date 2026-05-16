DELETE FROM vertex_bpmn_lexicon_binding WHERE process_id LIKE 'gftdcojp_personnel%';

DELETE FROM vertex_bpmn_process_def WHERE process_id LIKE 'gftdcojp_personnel%';

DROP MATERIALIZED VIEW IF EXISTS mv_gftdcojp_raci_by_task;

DROP MATERIALIZED VIEW IF EXISTS mv_gftdcojp_active_assignments;

DROP TABLE IF EXISTS vertex_gftdcojp_okr;

DROP TABLE IF EXISTS vertex_gftdcojp_raci;

DROP TABLE IF EXISTS vertex_gftdcojp_assignment;

DROP TABLE IF EXISTS vertex_gftdcojp_role;

DROP TABLE IF EXISTS vertex_gftdcojp_person;
