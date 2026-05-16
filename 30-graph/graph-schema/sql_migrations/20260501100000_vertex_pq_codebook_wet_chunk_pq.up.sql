CREATE TABLE IF NOT EXISTS vertex_pq_codebook (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      collection_id      VARCHAR NOT NULL,
      version_tag        VARCHAR NOT NULL,
      m_subspaces        BIGINT  NOT NULL DEFAULT 96,
      k_centroids        BIGINT  NOT NULL DEFAULT 256,
      dim                BIGINT  NOT NULL DEFAULT 768,
      subspace_dim       BIGINT  NOT NULL DEFAULT 8,
      n_train_vectors    BIGINT,
      codebook_json      VARCHAR,
      trained_at         VARCHAR,
      status             VARCHAR NOT NULL DEFAULT 'active'
    );

CREATE INDEX IF NOT EXISTS idx_pq_codebook_collection_status
      ON vertex_pq_codebook (collection_id, status);

CREATE TABLE IF NOT EXISTS vertex_wet_chunk_pq (
      pq_id              VARCHAR PRIMARY KEY,
      chunk_vertex_id    VARCHAR NOT NULL,
      ivf_cluster_id     BIGINT  NOT NULL,
      codebook_version   VARCHAR NOT NULL,
      domain             VARCHAR NOT NULL,
      pq_code            VARCHAR NOT NULL,
      encoded_at         VARCHAR NOT NULL
    ) APPEND ONLY;

CREATE INDEX IF NOT EXISTS idx_wet_chunk_pq_cluster
      ON vertex_wet_chunk_pq (ivf_cluster_id, codebook_version);

CREATE INDEX IF NOT EXISTS idx_wet_chunk_pq_domain
      ON vertex_wet_chunk_pq (domain, ivf_cluster_id, codebook_version);
