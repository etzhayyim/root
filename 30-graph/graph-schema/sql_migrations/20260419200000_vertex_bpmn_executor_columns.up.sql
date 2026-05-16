ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS process_id VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS xml_r2_key VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS json_r2_key VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS xsd_valid VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS deployed_at VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS deployed_by VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS deprecated VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS created_at VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS org_id VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS user_id VARCHAR;

ALTER TABLE vertex_bpmn_process ADD COLUMN IF NOT EXISTS actor_id VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS instance_id VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS process_id VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS state VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS variables_json VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS current_token_json VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS correlation_key VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS started_at VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS completed_at VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS error_code VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS waiting_json VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS created_at VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS org_id VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS user_id VARCHAR;

ALTER TABLE vertex_bpmn_instance ADD COLUMN IF NOT EXISTS actor_id VARCHAR;
