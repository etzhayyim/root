CREATE TABLE IF NOT EXISTS vertex_games_title (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      name VARCHAR,
      genre VARCHAR,
      publisher_did VARCHAR,
      platform VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_games_title_genre ON vertex_games_title (genre);

CREATE INDEX IF NOT EXISTS idx_games_title_publisher ON vertex_games_title (publisher_did);

CREATE TABLE IF NOT EXISTS vertex_games_score (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title_id VARCHAR,
      player_did VARCHAR,
      score BIGINT,
      level VARCHAR,
      mode VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_games_score_title_id ON vertex_games_score (title_id);

CREATE INDEX IF NOT EXISTS idx_games_score_player ON vertex_games_score (player_did);

CREATE INDEX IF NOT EXISTS idx_games_score_value ON vertex_games_score (score);
