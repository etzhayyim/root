ALTER TABLE vertex_patent_blob
      ADD COLUMN IF NOT EXISTS ocr_text VARCHAR;
