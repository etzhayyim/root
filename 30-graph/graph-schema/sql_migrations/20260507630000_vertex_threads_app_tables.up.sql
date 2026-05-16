CREATE TABLE IF NOT EXISTS vertex_threads_thread (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      author_did VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_threads_thread_id ON vertex_threads_thread (id);

CREATE INDEX IF NOT EXISTS idx_threads_thread_status ON vertex_threads_thread (status);

CREATE INDEX IF NOT EXISTS idx_threads_thread_author_did ON vertex_threads_thread (author_did);

CREATE TABLE IF NOT EXISTS vertex_threads_reply (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      thread_id VARCHAR,
      author_did VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_threads_reply_id ON vertex_threads_reply (id);

CREATE INDEX IF NOT EXISTS idx_threads_reply_thread_id ON vertex_threads_reply (thread_id);
