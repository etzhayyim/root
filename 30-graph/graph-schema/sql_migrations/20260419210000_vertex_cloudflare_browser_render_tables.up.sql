CREATE TABLE IF NOT EXISTS vertex_cloudflare_browser_render_session (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      session_id VARCHAR, durable_object_id VARCHAR, options VARCHAR,
      opened_at VARCHAR, expires_at VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_cloudflare_browser_render_artifact (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      artifact_id VARCHAR, url VARCHAR, output VARCHAR, cid VARCHAR, byte_size BIGINT, note VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );
