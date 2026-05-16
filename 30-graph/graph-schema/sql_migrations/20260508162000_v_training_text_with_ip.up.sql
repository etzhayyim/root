DROP VIEW IF EXISTS v_training_text;

CREATE VIEW v_training_text AS
      -- CommonCrawl WET markdown chunks
      SELECT
        vertex_id,
        'wet_chunk'                      AS label,
        markdown                         AS content,
        language                         AS lang,
        CAST(created_date AS VARCHAR)    AS created_date
      FROM vertex_wet_chunk
      WHERE sensitivity_ord = 0
        AND markdown IS NOT NULL
        AND markdown NOT LIKE 'signal:v1:%'
        AND LENGTH(markdown) >= 100
    UNION ALL
      -- Actor profile descriptions
      SELECT
        vertex_id,
        'profile'                        AS label,
        description                      AS content,
        NULL                             AS lang,
        CAST(created_date AS VARCHAR)    AS created_date
      FROM vertex_actor_profile
      WHERE sensitivity_ord = 0
        AND description IS NOT NULL
        AND description NOT LIKE 'signal:v1:%'
        AND LENGTH(description) >= 20
    UNION ALL
      -- HuggingFace dataset records (ADSK, etc.)
      SELECT
        vertex_id,
        'hf:' || slug                    AS label,
        text_for_training                AS content,
        lang                             AS lang,
        CAST(created_date AS VARCHAR)    AS created_date
      FROM vertex_hf_dataset_record
      WHERE sensitivity_ord = 0
        AND text_for_training IS NOT NULL
        AND text_for_training NOT LIKE 'signal:v1:%'
        AND LENGTH(text_for_training) >= 20
    UNION ALL
      -- Patent OCR text (pdftotext from USPTO/EPO PDFs)
      SELECT
        pb.vertex_id,
        'patent:' || p.jurisdiction      AS label,
        pb.ocr_text                      AS content,
        'en'                             AS lang,
        CAST(pb.created_date AS VARCHAR) AS created_date
      FROM vertex_patent_blob pb
      JOIN vertex_open_patent_patent p ON p.vertex_id = pb.patent_vertex_id
      WHERE pb.ocr_text IS NOT NULL
        AND pb.sensitivity_ord = 0
        AND LENGTH(pb.ocr_text) >= 100
        AND pb.ocr_text NOT LIKE 'signal:v1:%'
    UNION ALL
      -- Copyright open-access full text (CC-BY / public-domain)
      SELECT
        wb.vertex_id,
        'copyright:' || w.registry      AS label,
        wb.fulltext                      AS content,
        wb.lang                          AS lang,
        CAST(wb.created_date AS VARCHAR) AS created_date
      FROM vertex_work_blob wb
      JOIN vertex_work w ON w.vertex_id = wb.work_vertex_id
      WHERE wb.status = 'done'
        AND wb.fulltext IS NOT NULL
        AND wb.sensitivity_ord = 0
        AND LENGTH(wb.fulltext) >= 100
        AND wb.fulltext NOT LIKE 'signal:v1:%'
        AND wb.license IN (
          'cc-by', 'cc-by-sa', 'cc-by-nc', 'cc-by-nc-sa',
          'cc0', 'public-domain', 'cc-by-4.0', 'cc-by-sa-4.0'
        );
