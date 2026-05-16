DROP MATERIALIZED VIEW IF EXISTS mv_legal_corpus_jurisdiction_coverage;

ALTER TABLE vertex_legal_corpus_document ADD COLUMN IF NOT EXISTS embedding_vec vector(1024);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_legal_corpus_jurisdiction_coverage AS
      SELECT
        jurisdiction,
        source_id,
        COUNT(*) AS document_count,
        MAX(fetched_at) AS last_fetched_at
      FROM vertex_legal_corpus_document
      GROUP BY jurisdiction, source_id;
