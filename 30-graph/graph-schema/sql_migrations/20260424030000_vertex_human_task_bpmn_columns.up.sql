ALTER TABLE vertex_human_task
      ADD COLUMN IF NOT EXISTS zeebe_job_key BIGINT,
      ADD COLUMN IF NOT EXISTS bpmn_process_instance_key BIGINT,
      ADD COLUMN IF NOT EXISTS bpmn_process_definition_key BIGINT,
      ADD COLUMN IF NOT EXISTS bpmn_process_id VARCHAR,
      ADD COLUMN IF NOT EXISTS bpmn_element_id VARCHAR,
      ADD COLUMN IF NOT EXISTS form_key VARCHAR;

CREATE INDEX IF NOT EXISTS idx_vertex_human_task_zeebe_job_key
      ON vertex_human_task (zeebe_job_key)
      WHERE zeebe_job_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_vertex_human_task_bpmn_process_instance
      ON vertex_human_task (bpmn_process_instance_key)
      WHERE bpmn_process_instance_key IS NOT NULL;
