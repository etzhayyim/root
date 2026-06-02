CREATE TABLE IF NOT EXISTS vertex_projector_message (
      vertex_id VARCHAR PRIMARY KEY,
      uri VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      convo_id VARCHAR,
      sender_did VARCHAR,
      role VARCHAR,
      text TEXT,
      value_json TEXT,
      ts_ms BIGINT,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE INDEX IF NOT EXISTS idx_projector_message_convo_ts ON vertex_projector_message (convo_id, ts_ms);

CREATE INDEX IF NOT EXISTS idx_projector_message_repo ON vertex_projector_message (repo);

CREATE INDEX IF NOT EXISTS idx_projector_message_sender ON vertex_projector_message (sender_did);

INSERT INTO vertex_projector_message (
      vertex_id, uri, rkey, repo, convo_id, sender_did, role, text, value_json, ts_ms,
      created_at, owner_did, actor_id, sensitivity_ord
    )
    SELECT
      uri,
      uri,
      rkey,
      repo,
      coalesce(value_json::jsonb ->> 'convoId', ''),
      coalesce(value_json::jsonb ->> 'senderDid', value_json::jsonb ->> 'did', ''),
      coalesce(value_json::jsonb ->> 'role', ''),
      coalesce(value_json::jsonb ->> 'text', value_json::jsonb ->> 'content', ''),
      value_json,
      ts_ms,
      coalesce(value_json::jsonb ->> 'createdAt', created_at::text, indexed_at::text, ''),
      repo,
      'projector',
      2
    FROM vertex_repo_record
    WHERE collection = 'com.etzhayyim.convo.message'
      AND repo = 'did:web:ops.etzhayyim.com'
    ON CONFLICT (vertex_id) DO NOTHING;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_projector_message_convo_activity AS
    SELECT
      convo_id,
      count(*) AS message_count,
      max(ts_ms) AS latest_ts_ms
    FROM vertex_projector_message
    GROUP BY convo_id;
