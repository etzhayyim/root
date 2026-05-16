CREATE TABLE IF NOT EXISTS edge_projector_convo_message (
      edge_id VARCHAR PRIMARY KEY,
      convo_id VARCHAR NOT NULL,
      message_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      ts_ms BIGINT,
      created_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    );

CREATE INDEX IF NOT EXISTS idx_projector_convo_message_convo_ts ON edge_projector_convo_message (convo_id, ts_ms);

CREATE INDEX IF NOT EXISTS idx_projector_convo_message_msg ON edge_projector_convo_message (message_vid);

INSERT INTO edge_projector_convo_message (
      edge_id, convo_id, message_vid, relation_kind, ts_ms, created_at, owner_did, sensitivity_ord
    )
    SELECT
      concat('edge:projector:convo-message:', convo_id, ':', rkey),
      convo_id,
      vertex_id,
      'contains_message',
      ts_ms,
      created_at,
      owner_did,
      sensitivity_ord
    FROM vertex_projector_message
    WHERE convo_id IS NOT NULL AND convo_id <> ''
    ON CONFLICT (edge_id) DO NOTHING;
