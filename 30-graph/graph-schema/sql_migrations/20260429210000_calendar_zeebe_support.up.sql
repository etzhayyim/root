CREATE TABLE IF NOT EXISTS vertex_gcal_oauth_token (
      vertex_id VARCHAR PRIMARY KEY,
      account_did VARCHAR,
      email VARCHAR,
      encrypted_refresh_token VARCHAR,
      wrapped_data_key VARCHAR,
      iv VARCHAR,
      scope VARCHAR,
      access_token_cache VARCHAR,
      access_expires_at BIGINT,
      status VARCHAR,
      cursor VARCHAR,
      last_sync_at VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_gcal_oauth_token_email_status ON vertex_gcal_oauth_token (email, status);

CREATE INDEX IF NOT EXISTS idx_vertex_gcal_oauth_token_sync ON vertex_gcal_oauth_token (status, last_sync_at);
