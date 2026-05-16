CREATE TABLE IF NOT EXISTS vertex_music_track (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      artist_id VARCHAR,
      duration_sec BIGINT,
      genre VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_music_track_genre ON vertex_music_track (genre);

CREATE INDEX IF NOT EXISTS idx_music_track_artist_id ON vertex_music_track (artist_id);

CREATE TABLE IF NOT EXISTS vertex_music_artist (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      genre VARCHAR,
      country VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_music_artist_genre ON vertex_music_artist (genre);

CREATE INDEX IF NOT EXISTS idx_music_artist_status ON vertex_music_artist (status);
