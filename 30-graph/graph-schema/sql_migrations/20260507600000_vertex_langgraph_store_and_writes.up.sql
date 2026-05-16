CREATE TABLE IF NOT EXISTS vertex_langgraph_checkpoint_write (
      vertex_id    VARCHAR PRIMARY KEY,
      _seq         BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      thread_id    VARCHAR NOT NULL,
      checkpoint_id VARCHAR NOT NULL,
      checkpoint_ns VARCHAR NOT NULL DEFAULT '',
      task_id      VARCHAR NOT NULL,
      task_path    VARCHAR NOT NULL DEFAULT '',
      idx          INTEGER NOT NULL,
      channel      VARCHAR NOT NULL,
      type         VARCHAR NOT NULL DEFAULT 'json',
      blob         VARCHAR,
      created_at   VARCHAR,
      actor_did    VARCHAR,
      org_did      VARCHAR DEFAULT 'anon'
    );

CREATE INDEX IF NOT EXISTS idx_langgraph_write_lookup
      ON vertex_langgraph_checkpoint_write (thread_id, checkpoint_ns, checkpoint_id, idx ASC);

CREATE TABLE IF NOT EXISTS vertex_langgraph_store (
      vertex_id    VARCHAR PRIMARY KEY,
      _seq         BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      namespace    VARCHAR NOT NULL,
      key          VARCHAR NOT NULL,
      value        VARCHAR,
      created_at   VARCHAR,
      updated_at   VARCHAR,
      actor_did    VARCHAR,
      org_did      VARCHAR DEFAULT 'anon'
    );

CREATE INDEX IF NOT EXISTS idx_langgraph_store_ns
      ON vertex_langgraph_store (namespace, updated_at DESC);
