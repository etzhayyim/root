CREATE TABLE IF NOT EXISTS vertex_playwright_session (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      session_id VARCHAR, target VARCHAR, user_agent VARCHAR, locale VARCHAR, viewport_json VARCHAR,
      state VARCHAR, opened_at VARCHAR, closed_at VARCHAR, expires_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_playwright_action (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      action_id VARCHAR, session_id VARCHAR, op VARCHAR, args_json VARCHAR, result_json VARCHAR,
      state VARCHAR, error VARCHAR, enqueued_at VARCHAR, started_at VARCHAR, finished_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_playwright_artifact (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      artifact_id VARCHAR, session_id VARCHAR, kind VARCHAR, r2_key VARCHAR, cid VARCHAR,
      byte_size BIGINT, captured_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_playwright_action_in_session (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      action_id VARCHAR, session_id VARCHAR, created_at VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_playwright_artifact_in_session (
      edge_id VARCHAR PRIMARY KEY, src_vid VARCHAR, dst_vid VARCHAR,
      _seq BIGINT, created_date DATE, sensitivity_ord BIGINT, owner_did VARCHAR,
      artifact_id VARCHAR, session_id VARCHAR, created_at VARCHAR
    );
