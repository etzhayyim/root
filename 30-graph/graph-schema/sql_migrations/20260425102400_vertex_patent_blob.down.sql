DROP MATERIALIZED VIEW IF EXISTS mv_patent_coverage_by_year_jurisdiction;

DROP MATERIALIZED VIEW IF EXISTS mv_patent_blob_coverage;

DROP INDEX IF EXISTS idx_vertex_patent_blob_status;

DROP INDEX IF EXISTS idx_vertex_patent_blob_pdf_sha256;

DROP INDEX IF EXISTS idx_vertex_patent_blob_patent_vertex_id;

DROP TABLE IF EXISTS vertex_patent_blob;
