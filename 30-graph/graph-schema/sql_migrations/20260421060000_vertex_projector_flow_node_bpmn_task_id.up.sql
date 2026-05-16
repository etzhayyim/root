ALTER TABLE vertex_projector_flow_node
    ADD COLUMN IF NOT EXISTS bpmn_task_id VARCHAR;
