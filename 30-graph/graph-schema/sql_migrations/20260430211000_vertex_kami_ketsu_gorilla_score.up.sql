CREATE TABLE vertex_atrecord_kami_ketsu_gorilla_score (
      vertex_id  VARCHAR PRIMARY KEY,
      _seq       BIGINT NOT NULL,
      owner_did  VARCHAR NOT NULL,
      player_did VARCHAR NOT NULL,
      score      INTEGER NOT NULL,
      slaps      INTEGER NOT NULL,
      bananas    INTEGER NOT NULL,
      run_sec    DOUBLE PRECISION NOT NULL,
      created_at TIMESTAMPTZ NOT NULL
    );

CREATE INDEX idx_kami_ketsu_gorilla_score_rank
      ON vertex_atrecord_kami_ketsu_gorilla_score (score DESC, bananas DESC, run_sec ASC, created_at ASC);
