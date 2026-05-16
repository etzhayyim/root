CREATE TABLE IF NOT EXISTS vertex_outlook_connection (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      status VARCHAR,
      upn VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_outlook_connection_actor_did ON vertex_outlook_connection (actor_did);

CREATE INDEX IF NOT EXISTS idx_outlook_connection_status ON vertex_outlook_connection (status);

CREATE TABLE IF NOT EXISTS vertex_outlook_mailbox (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      connection_id VARCHAR,
      last_sync_at VARCHAR,
      message_count BIGINT,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_outlook_mailbox_connection_id ON vertex_outlook_mailbox (connection_id);

CREATE INDEX IF NOT EXISTS idx_outlook_mailbox_actor_did ON vertex_outlook_mailbox (actor_did);
