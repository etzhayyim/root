CREATE TABLE IF NOT EXISTS vertex_corpus_skill_node (
      node_id            VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      parent_id          VARCHAR,
      level              BIGINT  NOT NULL DEFAULT 0,
      domain             VARCHAR NOT NULL,
      summary            VARCHAR,
      doc_count          BIGINT  NOT NULL DEFAULT 0,
      centroid           REAL[],
      label              VARCHAR,
      keywords_csv       VARCHAR,
      distill_version    VARCHAR NOT NULL,
      status             VARCHAR NOT NULL DEFAULT 'active'
    );

CREATE INDEX IF NOT EXISTS idx_corpus_skill_node_parent
      ON vertex_corpus_skill_node (parent_id);

CREATE INDEX IF NOT EXISTS idx_corpus_skill_node_domain_level
      ON vertex_corpus_skill_node (domain, level, distill_version, status);

CREATE TABLE IF NOT EXISTS edge_skill_doc (
      edge_id            VARCHAR PRIMARY KEY,
      node_id            VARCHAR NOT NULL,
      chunk_vertex_id    VARCHAR NOT NULL,
      domain             VARCHAR NOT NULL,
      cluster_id         BIGINT,
      distill_version    VARCHAR NOT NULL,
      distance           DOUBLE PRECISION
    );

CREATE INDEX IF NOT EXISTS idx_edge_skill_doc_node
      ON edge_skill_doc (node_id, distill_version);

CREATE INDEX IF NOT EXISTS idx_edge_skill_doc_cluster
      ON edge_skill_doc (domain, cluster_id, distill_version);
