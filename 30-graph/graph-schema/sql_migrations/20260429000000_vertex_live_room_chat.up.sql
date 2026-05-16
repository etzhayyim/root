CREATE TABLE IF NOT EXISTS vertex_live_room (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      slug VARCHAR NOT NULL,
      bpm DOUBLE PRECISION NOT NULL,
      start_at DOUBLE PRECISION NOT NULL,
      stage_preset VARCHAR NOT NULL,
      performer_handle VARCHAR,
      setlist_json TEXT,
      lighting_json TEXT,
      crowd_seed BIGINT,
      fans_target BIGINT,
      name VARCHAR,
      description VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      at_did VARCHAR,
      created_at VARCHAR NOT NULL
    );

CREATE TABLE IF NOT EXISTS vertex_live_chat (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      room_slug VARCHAR NOT NULL,
      actor_handle VARCHAR NOT NULL,
      text VARCHAR NOT NULL,
      kind VARCHAR,
      tint_r DOUBLE PRECISION,
      tint_g DOUBLE PRECISION,
      tint_b DOUBLE PRECISION,
      posted_at DOUBLE PRECISION NOT NULL,
      name VARCHAR,
      description VARCHAR,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      at_did VARCHAR,
      created_at VARCHAR NOT NULL
    );

INSERT INTO vertex_live_room (
      vertex_id, slug, bpm, start_at, stage_preset, performer_handle,
      setlist_json, lighting_json, crowd_seed, fans_target,
      name, description, actor_did, org_did, at_did, created_at
    )
    VALUES (
      'at://did:web:live.gftd.ai/ai.gftd.apps.live.room/demo',
      'demo',
      128.0,
      1777380000.0,
      'hall',
      'Mitama',
      '[]',
      '[]',
      7,
      600,
      'live demo room',
      'Open virtual concert room — mitama actors join, dance, converse via the BPMN show flow at apps/live/showFlow.bpmn.',
      'did:web:live.gftd.ai',
      'anon',
      'did:web:live.gftd.ai',
      '2026-04-29T00:00:00Z'
    );
