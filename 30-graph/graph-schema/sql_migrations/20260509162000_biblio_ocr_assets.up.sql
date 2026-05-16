CREATE TABLE IF NOT EXISTS vertex_biblio_page_asset (
  vertex_id varchar PRIMARY KEY,
  _seq bigint,
  created_date date,
  sensitivity_ord int,
  owner_did varchar,
  source_id varchar NOT NULL,
  source_record_id varchar NOT NULL,
  page_index int NOT NULL,
  source_image_url varchar NOT NULL,
  webp_sha256 varchar,
  webp_cid_v1 varchar,
  webp_b2_bucket varchar,
  webp_b2_key varchar,
  webp_byte_size bigint,
  width_px int,
  height_px int,
  ocr_status varchar NOT NULL,
  status varchar NOT NULL,
  created_at varchar,
  updated_at varchar,
  org_id varchar,
  user_id varchar,
  actor_id varchar
);

CREATE INDEX IF NOT EXISTS idx_biblio_page_asset_record
  ON vertex_biblio_page_asset (source_id, source_record_id, page_index);

CREATE TABLE IF NOT EXISTS vertex_biblio_ocr_text (
  vertex_id varchar PRIMARY KEY,
  _seq bigint,
  created_date date,
  sensitivity_ord int,
  owner_did varchar,
  source_id varchar NOT NULL,
  source_record_id varchar NOT NULL,
  page_index int NOT NULL,
  ocr_engine varchar NOT NULL,
  ocr_model varchar,
  ocr_text varchar,
  ocr_json varchar,
  warnings varchar,
  text_sha256 varchar,
  text_byte_size bigint,
  status varchar NOT NULL,
  created_at varchar,
  org_id varchar,
  user_id varchar,
  actor_id varchar
);

CREATE INDEX IF NOT EXISTS idx_biblio_ocr_record
  ON vertex_biblio_ocr_text (source_id, source_record_id, page_index);

GRANT SELECT, INSERT, UPDATE ON vertex_biblio_page_asset TO root;
GRANT SELECT, INSERT, UPDATE ON vertex_biblio_ocr_text TO root;
