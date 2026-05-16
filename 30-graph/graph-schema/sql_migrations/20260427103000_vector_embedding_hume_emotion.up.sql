CREATE TABLE IF NOT EXISTS vertex_vector_emotion_signal (
      signal_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       INT,
      owner_did             VARCHAR,

      source_uri            VARCHAR NOT NULL,
      source_vertex_id      VARCHAR,
      tenant_id             VARCHAR DEFAULT 'public',
      shard_id              INT,
      modality              VARCHAR NOT NULL,
      provider              VARCHAR NOT NULL,
      model_id              VARCHAR NOT NULL,
      model_version         VARCHAR,
      granularity           VARCHAR,
      language              VARCHAR,
      top_emotion           VARCHAR,
      top_score             DOUBLE PRECISION,
      scores_json           VARCHAR,
      raw_json              VARCHAR,
      analyzed_at           VARCHAR,

      org_id                VARCHAR DEFAULT 'anon',
      user_id               VARCHAR DEFAULT 'anon',
      actor_id              VARCHAR DEFAULT '',
      created_at            VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vector_emotion_signal_source
    ON vertex_vector_emotion_signal(source_uri, model_id);

CREATE INDEX IF NOT EXISTS idx_vector_emotion_signal_top
    ON vertex_vector_emotion_signal(top_emotion, top_score);

CREATE INDEX IF NOT EXISTS idx_vector_emotion_signal_shard
    ON vertex_vector_emotion_signal(tenant_id, shard_id, modality);

INSERT INTO vertex_vector_embedding_model (
      vertex_id, model_id, provider, model_family, model_name, model_version,
      model_uri, license, base_anchor, supported_modalities, native_dimension,
      stored_dimension, distance_type, pooling, normalization, context_length,
      commercial_use, status, notes, created_at
    )
    SELECT
      'model:hume-emotional-language',
      'hume-emotional-language',
      'Hume AI',
      'expression-measurement',
      'Hume Emotional Language',
      'initial',
      'https://dev.hume.ai/docs/expression-measurement/models/language',
      'proprietary-api',
      'text',
      'text,audio,video',
      53,
      0,
      'none',
      'emotion-scores',
      'none',
      NULL::INT,
      'api-commercial-terms',
      'active',
      'Expression Measurement emotional-language scores stored as non-vector enrichment for vector embedding sources.',
      '2026-04-27'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_vector_embedding_model
      WHERE model_id = 'hume-emotional-language'
    );

FLUSH;
