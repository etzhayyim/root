CREATE TABLE IF NOT EXISTS vertex_gameka_studio_config (
      vertex_id VARCHAR PRIMARY KEY, _seq BIGINT, created_date DATE, sensitivity_ord BIGINT,
      owner_did VARCHAR, rkey VARCHAR, repo VARCHAR,
      config_id VARCHAR, tick_live_mode BOOLEAN,
      max_iterations BIGINT, score_threshold DOUBLE PRECISION,
      note VARCHAR,
      created_at VARCHAR, org_id VARCHAR, user_id VARCHAR, actor_id VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_gameka_studio_config_id
      ON vertex_gameka_studio_config (config_id);

INSERT INTO vertex_gameka_studio_config (
      vertex_id, owner_did, rkey, repo,
      config_id, tick_live_mode,
      max_iterations, score_threshold,
      note, created_at
    ) VALUES (
      'at://did:web:gameka.etzhayyim.com/com.etzhayyim.apps.gameka.studioConfig/global',
      'did:web:gameka.etzhayyim.com', 'global', 'did:web:gameka.etzhayyim.com',
      'global', false,
      3, 0.8,
      'P7 dry-run seed — flip tick_live_mode=true after 14-day soak.',
      '2026-04-25T00:00:00Z'
    );
