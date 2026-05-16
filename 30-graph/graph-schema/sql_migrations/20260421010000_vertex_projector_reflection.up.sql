CREATE TABLE IF NOT EXISTS vertex_projector_reflection (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      convo_id VARCHAR, attempt VARCHAR, outcome VARCHAR, reflection VARCHAR,
      created_by VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_projector_reflection_convo
            ON vertex_projector_reflection (convo_id, _seq);
