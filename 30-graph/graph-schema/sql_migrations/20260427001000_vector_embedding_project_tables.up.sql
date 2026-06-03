CREATE TABLE IF NOT EXISTS vertex_vector_embedding_model (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       INT,
      owner_did             VARCHAR,

      model_id              VARCHAR NOT NULL,
      provider              VARCHAR NOT NULL,
      model_family          VARCHAR NOT NULL,
      model_name            VARCHAR NOT NULL,
      model_version         VARCHAR,
      model_uri             VARCHAR,
      license               VARCHAR,
      base_anchor           VARCHAR,
      supported_modalities  VARCHAR NOT NULL,
      native_dimension      INT NOT NULL,
      stored_dimension      INT NOT NULL,
      distance_type         VARCHAR NOT NULL,
      pooling               VARCHAR,
      normalization         VARCHAR,
      context_length        INT,
      commercial_use        VARCHAR,
      status                VARCHAR NOT NULL,
      notes                 VARCHAR,

      org_id                VARCHAR DEFAULT 'anon',
      user_id               VARCHAR DEFAULT 'anon',
      actor_id              VARCHAR DEFAULT '',
      created_at            VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_vector_embedding_space (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       INT,
      owner_did             VARCHAR,

      space_id              VARCHAR NOT NULL,
      space_kind            VARCHAR NOT NULL,
      description           VARCHAR,
      anchor_model_id       VARCHAR,
      anchor_modality       VARCHAR,
      dimension             INT NOT NULL,
      distance_type         VARCHAR NOT NULL,
      normalization         VARCHAR NOT NULL,
      modality_scope        VARCHAR NOT NULL,
      status                VARCHAR NOT NULL,
      created_at            VARCHAR,

      org_id                VARCHAR DEFAULT 'anon',
      user_id               VARCHAR DEFAULT 'anon',
      actor_id              VARCHAR DEFAULT ''
    );

CREATE TABLE IF NOT EXISTS vertex_vector_embedding_source (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       INT,
      owner_did             VARCHAR,

      source_uri            VARCHAR NOT NULL,
      source_cid            VARCHAR,
      source_kind           VARCHAR NOT NULL,
      source_table          VARCHAR,
      source_vertex_id      VARCHAR,
      source_collection     VARCHAR,
      repo                  VARCHAR,
      rkey                  VARCHAR,
      tenant_id             VARCHAR DEFAULT 'public',
      shard_id              INT,
      modality              VARCHAR NOT NULL,
      media_type            VARCHAR,
      lang                  VARCHAR,
      text_preview          VARCHAR,
      content_hash          VARCHAR,
      blob_ref              VARCHAR,
      width_px              INT,
      height_px             INT,
      duration_ms           BIGINT,
      sample_rate_hz        INT,
      frame_rate_millis     INT,
      sensor_vendor         VARCHAR,
      sensor_model          VARCHAR,
      sensor_frame          VARCHAR,
      captured_at           VARCHAR,
      indexed_at            VARCHAR,
      visibility            VARCHAR DEFAULT 'public',
      safety_label          VARCHAR,
      metadata_json         VARCHAR,

      org_id                VARCHAR DEFAULT 'anon',
      user_id               VARCHAR DEFAULT 'anon',
      actor_id              VARCHAR DEFAULT '',
      created_at            VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_vector_embedding_chunk (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       INT,
      owner_did             VARCHAR,

      chunk_id              VARCHAR NOT NULL,
      source_uri            VARCHAR NOT NULL,
      source_vertex_id      VARCHAR,
      modality              VARCHAR NOT NULL,
      chunk_kind            VARCHAR NOT NULL,
      chunk_index           INT NOT NULL,
      chunk_uri             VARCHAR,
      text                  VARCHAR,
      start_offset          BIGINT,
      end_offset            BIGINT,
      start_ms              BIGINT,
      end_ms                BIGINT,
      frame_index           BIGINT,
      page_index            INT,
      bbox_json             VARCHAR,
      sensor_axis_json      VARCHAR,
      metadata_json         VARCHAR,

      org_id                VARCHAR DEFAULT 'anon',
      user_id               VARCHAR DEFAULT 'anon',
      actor_id              VARCHAR DEFAULT '',
      created_at            VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_vector_embedding_projection (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       INT,
      owner_did             VARCHAR,

      projection_id         VARCHAR NOT NULL,
      source_model_id       VARCHAR NOT NULL,
      target_space_id       VARCHAR NOT NULL,
      projection_kind       VARCHAR NOT NULL,
      source_dimension      INT NOT NULL,
      target_dimension      INT NOT NULL,
      projection_ref        VARCHAR,
      training_dataset_ref  VARCHAR,
      loss_name             VARCHAR,
      eval_json             VARCHAR,
      status                VARCHAR NOT NULL,
      created_at            VARCHAR,

      org_id                VARCHAR DEFAULT 'anon',
      user_id               VARCHAR DEFAULT 'anon',
      actor_id              VARCHAR DEFAULT ''
    );

CREATE TABLE IF NOT EXISTS vertex_vector_embedding_768 (
      embedding_id          VARCHAR,
      source_uri            VARCHAR,
      chunk_id              VARCHAR,
      source_vertex_id      VARCHAR,
      tenant_id             VARCHAR,
      shard_id              INT,
      modality              VARCHAR,
      model_id              VARCHAR,
      space_id              VARCHAR,
      model_version         VARCHAR,
      projection_id         VARCHAR,
      emb                   vector(768),
      text_preview          VARCHAR,
      created_at            VARCHAR,
      embedded_at           VARCHAR
    ) APPEND ONLY;

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vector_embedding_model_id
    ON vertex_vector_embedding_model(model_id);

CREATE INDEX IF NOT EXISTS idx_vector_embedding_space_id
    ON vertex_vector_embedding_space(space_id);

CREATE INDEX IF NOT EXISTS idx_vector_embedding_source_uri
    ON vertex_vector_embedding_source(source_uri);

CREATE INDEX IF NOT EXISTS idx_vector_embedding_source_modality
    ON vertex_vector_embedding_source(modality);

CREATE INDEX IF NOT EXISTS idx_vector_embedding_source_shard
    ON vertex_vector_embedding_source(tenant_id, shard_id, modality);

CREATE INDEX IF NOT EXISTS idx_vector_embedding_chunk_source
    ON vertex_vector_embedding_chunk(source_uri);

CREATE INDEX IF NOT EXISTS idx_vector_embedding_projection_model
    ON vertex_vector_embedding_projection(source_model_id, target_space_id);

CREATE INDEX IF NOT EXISTS idx_vector_embedding_768_lookup
    ON vertex_vector_embedding_768(source_uri, chunk_id, model_id, space_id);

CREATE INDEX IF NOT EXISTS idx_vector_embedding_768_shard
    ON vertex_vector_embedding_768(tenant_id, shard_id, modality, space_id);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vector_embedding_768_hnsw
    ON vertex_vector_embedding_768
    USING HNSW (emb)
    INCLUDE (embedding_id, source_uri, chunk_id, source_vertex_id, tenant_id, shard_id, modality, model_id, space_id, model_version, text_preview, created_at)
    WITH (distance_type = 'cosine', m = 16, ef_construction = 200);

FLUSH;

INSERT INTO vertex_vector_embedding_model (
      vertex_id, model_id, provider, model_family, model_name, model_version,
      model_uri, license, base_anchor, supported_modalities, native_dimension,
      stored_dimension, distance_type, pooling, normalization, context_length,
      commercial_use, status, notes, created_at
    ) VALUES
      (
        'model:bge-m3',
        'bge-m3',
        'BAAI',
        'bge',
        'BAAI/bge-m3',
        'initial',
        'https://huggingface.co/BAAI/bge-m3',
        'MIT',
        'text',
        'text',
        1024,
        768,
        'cosine',
        'dense',
        'l2',
        8192,
        'allowed',
        'active',
        'Primary text retrieval model; stored as 768d in etzhayyim-mm-768 via projection/truncation.',
        '2026-04-26'
      ),
      (
        'model:openclip-vit-b-32',
        'openclip-vit-b-32',
        'OpenCLIP',
        'clip',
        'OpenCLIP ViT-B-32',
        'initial',
        'https://github.com/mlfoundations/open_clip',
        'open-source',
        'image-text',
        'text,image',
        512,
        768,
        'cosine',
        'pooled',
        'l2',
        77,
        'check-model-license',
        'candidate',
        'Initial image/text candidate; projected into etzhayyim-mm-768 before storage.',
        '2026-04-26'
      ),
      (
        'model:qwen3-vl-embedding-2b',
        'qwen3-vl-embedding-2b',
        'Qwen',
        'qwen3-vl',
        'Qwen/Qwen3-VL-Embedding-2B',
        'initial',
        'https://huggingface.co/Qwen/Qwen3-VL-Embedding-2B',
        'Apache-2.0',
        'vision-language',
        'text,image,screenshot,video,mixed',
        2048,
        768,
        'cosine',
        'instruction-aware',
        'l2',
        32768,
        'allowed',
        'candidate',
        'Candidate anchor for production image/video/screenshot retrieval and future sensor projection.',
        '2026-04-26'
      ),
      (
        'model:imagebind-huge',
        'imagebind-huge',
        'Meta',
        'imagebind',
        'ImageBind Huge',
        'initial',
        'https://github.com/facebookresearch/ImageBind',
        'CC-BY-NC-4.0',
        'image',
        'text,image,video,audio,depth,thermal,imu',
        1024,
        768,
        'cosine',
        'pooled',
        'l2',
        77,
        'non-commercial-only',
        'experimental',
        'Sensor-inclusive research baseline; projected into etzhayyim-mm-768 for experiments only.',
        '2026-04-26'
      );

INSERT INTO vertex_vector_embedding_space (
      vertex_id, space_id, space_kind, description, anchor_model_id,
      anchor_modality, dimension, distance_type, normalization, modality_scope,
      status, created_at
    ) VALUES
      (
        'space:etzhayyim-mm-768',
        'etzhayyim-mm-768',
        'unified-projection',
        'Phase 1 production 768d multimodal search space. Text/image/video are active first; audio/depth/thermal/IMU arrive through later adapters.',
        'qwen3-vl-embedding-2b',
        'vision-language',
        768,
        'cosine',
        'l2',
        'text,image,video,audio,depth,thermal,imu,sensor',
        'active',
        '2026-04-26'
      );

INSERT INTO vertex_vector_embedding_projection (
      vertex_id, projection_id, source_model_id, target_space_id,
      projection_kind, source_dimension, target_dimension, projection_ref,
      training_dataset_ref, loss_name, eval_json, status, created_at
    ) VALUES
      (
        'projection:bge-m3-to-etzhayyim-mm-768',
        'bge-m3-to-etzhayyim-mm-768',
        'bge-m3',
        'etzhayyim-mm-768',
        'truncate-mrl-or-pca',
        1024,
        768,
        'etzhayyim-project-vector-embedding/projections/bge-m3-to-etzhayyim-mm-768',
        NULL,
        'cosine',
        NULL,
        'planned',
        '2026-04-26'
      ),
      (
        'projection:openclip-to-etzhayyim-mm-768',
        'openclip-to-etzhayyim-mm-768',
        'openclip-vit-b-32',
        'etzhayyim-mm-768',
        'linear-adapter',
        512,
        768,
        'etzhayyim-project-vector-embedding/projections/openclip-to-etzhayyim-mm-768',
        NULL,
        'infonce',
        NULL,
        'planned',
        '2026-04-26'
      ),
      (
        'projection:qwen3-vl-to-etzhayyim-mm-768',
        'qwen3-vl-to-etzhayyim-mm-768',
        'qwen3-vl-embedding-2b',
        'etzhayyim-mm-768',
        'mrl-or-linear-adapter',
        2048,
        768,
        'etzhayyim-project-vector-embedding/projections/qwen3-vl-to-etzhayyim-mm-768',
        NULL,
        'cosine',
        NULL,
        'planned',
        '2026-04-26'
      );

FLUSH;
