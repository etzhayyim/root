CREATE TABLE IF NOT EXISTS vertex_projector_flow (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      flow_key VARCHAR, name VARCHAR, description VARCHAR, version BIGINT,
      bpmn_task_id VARCHAR, bpmn_process_id VARCHAR,
      entry_node VARCHAR, status VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_projector_flow_node (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      flow_vertex_id VARCHAR, node_key VARCHAR, node_type VARCHAR,
      model_id VARCHAR, temperature_bps BIGINT, max_tokens BIGINT,
      prompt_template VARCHAR, tools_json VARCHAR, config_json VARCHAR,
      retry_max BIGINT, timeout_ms BIGINT,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_projector_flow_edge (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      flow_vertex_id VARCHAR, condition_expr VARCHAR, priority BIGINT,
      edge_kind VARCHAR,
      created_at VARCHAR, org_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_projector_flow_run (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      flow_vertex_id VARCHAR, parent_run_id VARCHAR,
      status VARCHAR, current_node VARCHAR, vars_json VARCHAR,
      convo_id VARCHAR, project_id VARCHAR,
      started_at VARCHAR, resume_at VARCHAR, finished_at VARCHAR,
      error_code VARCHAR, error_message VARCHAR,
      runner_kind VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_projector_flow_step (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      run_vertex_id VARCHAR, node_key VARCHAR, node_type VARCHAR,
      attempt BIGINT, status VARCHAR,
      input_json VARCHAR, output_json VARCHAR,
      model_id VARCHAR, prompt_tokens BIGINT, completion_tokens BIGINT, total_tokens BIGINT,
      latency_ms BIGINT,
      ocel_event_id VARCHAR, bpmn_activity_id VARCHAR,
      started_at VARCHAR, finished_at VARCHAR,
      error_code VARCHAR, error_message VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_projector_flow_run_resume
            ON vertex_projector_flow_run (status, resume_at);

CREATE INDEX IF NOT EXISTS idx_projector_flow_run_flow
            ON vertex_projector_flow_run (flow_vertex_id);

CREATE INDEX IF NOT EXISTS idx_projector_flow_step_run
            ON vertex_projector_flow_step (run_vertex_id, _seq);

CREATE INDEX IF NOT EXISTS idx_projector_flow_node_flow
            ON vertex_projector_flow_node (flow_vertex_id, node_key);

CREATE INDEX IF NOT EXISTS idx_projector_flow_edge_flow
            ON edge_projector_flow_edge (flow_vertex_id, src_vid);
