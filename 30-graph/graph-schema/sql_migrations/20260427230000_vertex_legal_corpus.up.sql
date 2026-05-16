CREATE TABLE vertex_legal_corpus_source (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      source_id          varchar NOT NULL,
      display_name       varchar NOT NULL,
      base_url           varchar NOT NULL,
      jurisdictions_csv  varchar,
      cadence_iso8601    varchar NOT NULL,
      auth_strategy      varchar NOT NULL,
      secret_ref         varchar,
      license            varchar,
      last_cursor        varchar,
      last_fetched_at    varchar,
      status             varchar NOT NULL,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE TABLE vertex_legal_corpus_document (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      source_id          varchar NOT NULL,
      canonical_uri      varchar NOT NULL,
      document_type      varchar NOT NULL,
      jurisdiction       varchar NOT NULL,
      court              varchar,
      court_did          varchar,
      language_code      varchar NOT NULL,
      title              varchar NOT NULL,
      citation           varchar,
      decided_at         varchar,
      published_at       varchar,
      fetched_at         varchar NOT NULL,
      body_text          varchar,
      body_uri           varchar,
      body_byte_size     bigint,
      topic_tags_csv     varchar,
      embedding          real[],
      embedding_dim      int,
      embedding_model    varchar,
      embedding_at       varchar,
      ivf_cluster_id     int,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE INDEX idx_legal_corpus_doc_source_uri ON vertex_legal_corpus_document(source_id, canonical_uri);

CREATE INDEX idx_legal_corpus_doc_jurisdiction ON vertex_legal_corpus_document(jurisdiction);

CREATE INDEX idx_legal_corpus_doc_decided_at ON vertex_legal_corpus_document(decided_at);

CREATE INDEX idx_legal_corpus_doc_ivf_cluster ON vertex_legal_corpus_document(ivf_cluster_id);

CREATE TABLE vertex_legal_corpus_document_pii (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      document_vid       varchar NOT NULL,
      parties_enc        varchar,
      judge_names_enc    varchar,
      counsel_names_enc  varchar,
      sealing_order      varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE INDEX idx_legal_corpus_pii_doc ON vertex_legal_corpus_document_pii(document_vid);

CREATE TABLE edge_legal_corpus_cites (
      edge_id            varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      src_vid            varchar NOT NULL,
      dst_vid            varchar NOT NULL,
      cite_kind          varchar,
      treatment          varchar,
      pinpoint           varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    );

CREATE INDEX idx_legal_corpus_cites_src ON edge_legal_corpus_cites(src_vid);

CREATE INDEX idx_legal_corpus_cites_dst ON edge_legal_corpus_cites(dst_vid);

CREATE MATERIALIZED VIEW mv_legal_corpus_jurisdiction_coverage AS
      SELECT
        jurisdiction,
        source_id,
        COUNT(*) AS document_count,
        MAX(fetched_at) AS last_fetched_at
      FROM vertex_legal_corpus_document
      GROUP BY jurisdiction, source_id;
