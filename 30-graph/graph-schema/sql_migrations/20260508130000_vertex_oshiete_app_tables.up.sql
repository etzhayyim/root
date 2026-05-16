CREATE TABLE IF NOT EXISTS vertex_oshiete_question (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      title VARCHAR,
      body VARCHAR,
      topic VARCHAR,
      status VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_oshiete_question_topic ON vertex_oshiete_question (topic);

CREATE INDEX IF NOT EXISTS idx_oshiete_question_status ON vertex_oshiete_question (status);

CREATE INDEX IF NOT EXISTS idx_oshiete_question_actor_did ON vertex_oshiete_question (actor_did);

CREATE TABLE IF NOT EXISTS vertex_oshiete_answer (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      id VARCHAR,
      question_id VARCHAR,
      body VARCHAR,
      vote_count BIGINT,
      actor_did VARCHAR,
      org_did VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_oshiete_answer_question_id ON vertex_oshiete_answer (question_id);

CREATE INDEX IF NOT EXISTS idx_oshiete_answer_actor_did ON vertex_oshiete_answer (actor_did);
