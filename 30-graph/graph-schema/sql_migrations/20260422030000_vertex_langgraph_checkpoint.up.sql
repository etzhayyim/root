CREATE TABLE IF NOT EXISTS vertex_langgraph_checkpoint (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      thread_id VARCHAR, checkpoint_id VARCHAR, checkpoint_ns VARCHAR,
      parent_checkpoint_id VARCHAR, checkpoint_type VARCHAR,
      blob VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_langgraph_checkpoint_thread_cid
      ON vertex_langgraph_checkpoint (thread_id, checkpoint_id DESC);

CREATE INDEX IF NOT EXISTS idx_langgraph_checkpoint_parent
      ON vertex_langgraph_checkpoint (parent_checkpoint_id);
