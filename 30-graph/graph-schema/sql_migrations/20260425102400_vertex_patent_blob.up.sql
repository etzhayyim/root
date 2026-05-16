CREATE TABLE vertex_patent_blob (
      vertex_id varchar PRIMARY KEY,
      _seq bigint,
      created_date date,
      sensitivity_ord int,
      owner_did varchar,

      patent_vertex_id varchar NOT NULL,
      patent_number varchar NOT NULL,
      jurisdiction varchar NOT NULL,

      pdf_sha256 varchar,
      pdf_bytes bigint,
      pdf_page_count int,
      pdf_source_url varchar,

      webp_cid varchar,
      webp_bytes bigint,
      webp_quality int,

      ocr_text_cid varchar,
      ocr_engine varchar,

      status varchar NOT NULL,
      last_error varchar,
      collected_at varchar
    );

CREATE INDEX idx_vertex_patent_blob_patent_vertex_id
      ON vertex_patent_blob(patent_vertex_id);

CREATE INDEX idx_vertex_patent_blob_pdf_sha256
      ON vertex_patent_blob(pdf_sha256);

CREATE INDEX idx_vertex_patent_blob_status
      ON vertex_patent_blob(status);

CREATE MATERIALIZED VIEW mv_patent_blob_coverage AS
      SELECT
        jurisdiction,
        COUNT(*) AS total,
        COUNT(pdf_sha256) AS pdf_fetched,
        COUNT(webp_cid) AS webp_done,
        COUNT(ocr_text_cid) AS ocr_done,
        SUM(pdf_bytes) AS bytes_pdf,
        SUM(webp_bytes) AS bytes_webp
      FROM vertex_patent_blob
      GROUP BY jurisdiction;

CREATE MATERIALIZED VIEW mv_patent_coverage_by_year_jurisdiction AS
      SELECT
        jurisdiction,
        SUBSTRING(filing_date, 1, 4) AS filing_year,
        COUNT(*) AS app_count,
        COUNT(grant_date) AS granted_count,
        AVG(novelty_score) AS avg_novelty
      FROM vertex_open_patent_patent
      WHERE filing_date IS NOT NULL
      GROUP BY jurisdiction, SUBSTRING(filing_date, 1, 4);
