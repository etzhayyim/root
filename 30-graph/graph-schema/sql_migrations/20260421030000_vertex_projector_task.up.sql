CREATE TABLE IF NOT EXISTS vertex_projector_task (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      convo_id VARCHAR, title VARCHAR, status VARCHAR, priority VARCHAR,
      assignee_did VARCHAR, due_date VARCHAR,
      completed_by VARCHAR, completed_at VARCHAR, created_by VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_projector_task_convo_status
            ON vertex_projector_task (convo_id, status);
