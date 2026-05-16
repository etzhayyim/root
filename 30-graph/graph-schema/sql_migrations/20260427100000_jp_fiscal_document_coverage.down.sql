DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_collection_ingest_coverage;

DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_source_document_coverage;

DROP INDEX IF EXISTS idx_edge_jp_fiscal_evidence_dst_kind;

DROP INDEX IF EXISTS idx_edge_jp_fiscal_evidence_src_kind;

DROP INDEX IF EXISTS idx_jp_fiscal_document_sha;
