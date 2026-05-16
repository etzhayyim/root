CREATE TABLE IF NOT EXISTS vertex_corpus_skill_extraction_run (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      label              VARCHAR,
      source_table       VARCHAR,
      source_actor_did   VARCHAR,
      extractor_version  VARCHAR,
      model_id           VARCHAR,
      params_json        VARCHAR,
      corpus_limit       BIGINT,
      skill_limit        BIGINT,
      min_score          DOUBLE PRECISION,
      matched_documents  BIGINT,
      emitted_edges      BIGINT,
      status             VARCHAR,
      started_at         VARCHAR,
      finished_at        VARCHAR,
      props              VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_corpus_skill_evidence (
      edge_id             VARCHAR PRIMARY KEY,
      corpus_vertex_id    VARCHAR NOT NULL,
      corpus_table        VARCHAR NOT NULL,
      skill_id            VARCHAR NOT NULL,
      extraction_run_id   VARCHAR,
      source_actor_did    VARCHAR,
      match_kind          VARCHAR,
      score               DOUBLE PRECISION,
      evidence_text       VARCHAR,
      evidence_start      BIGINT,
      evidence_end        BIGINT,
      source              VARCHAR,
      source_license      VARCHAR,
      ingested_at         VARCHAR,
      props               VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_corpus_skill_evidence_corpus
      ON edge_corpus_skill_evidence (corpus_table, corpus_vertex_id);

CREATE INDEX IF NOT EXISTS idx_edge_corpus_skill_evidence_skill
      ON edge_corpus_skill_evidence (skill_id);

CREATE INDEX IF NOT EXISTS idx_edge_corpus_skill_evidence_run
      ON edge_corpus_skill_evidence (extraction_run_id);
