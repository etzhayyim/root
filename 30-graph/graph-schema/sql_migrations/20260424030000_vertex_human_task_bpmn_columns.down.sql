DROP INDEX IF EXISTS idx_vertex_human_task_bpmn_process_instance;

DROP INDEX IF EXISTS idx_vertex_human_task_zeebe_job_key;

ALTER TABLE vertex_human_task
      DROP COLUMN IF EXISTS form_key,
      DROP COLUMN IF EXISTS bpmn_element_id,
      DROP COLUMN IF EXISTS bpmn_process_id,
      DROP COLUMN IF EXISTS bpmn_process_definition_key,
      DROP COLUMN IF EXISTS bpmn_process_instance_key,
      DROP COLUMN IF EXISTS zeebe_job_key;
