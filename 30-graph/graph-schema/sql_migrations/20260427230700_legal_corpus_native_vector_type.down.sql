ALTER TABLE vertex_legal_corpus_document DROP COLUMN IF EXISTS embedding;

ALTER TABLE vertex_legal_corpus_document ADD COLUMN embedding real[];
