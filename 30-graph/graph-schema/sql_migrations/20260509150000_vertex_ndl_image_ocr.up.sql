CREATE TABLE IF NOT EXISTS vertex_ndl_digital_item (
  vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
  pid varchar NOT NULL,
  provider_id varchar NOT NULL,
  repository_no varchar,
  title varchar,
  creator varchar,
  issued varchar,
  language varchar,
  material_type varchar,
  access_scope varchar,
  content_license varchar,
  source_url varchar,
  manifest_url varchar,
  record_xml_sha256 varchar,
  status varchar NOT NULL,
  discovered_at varchar,
  updated_at varchar,
  org_id varchar, user_id varchar, actor_id varchar
);

CREATE TABLE IF NOT EXISTS vertex_ndl_digital_page (
  vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
  pid varchar NOT NULL,
  provider_id varchar NOT NULL,
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
  org_id varchar, user_id varchar, actor_id varchar
);

CREATE TABLE IF NOT EXISTS vertex_ndl_ocr_text (
  vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
  pid varchar NOT NULL,
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
  org_id varchar, user_id varchar, actor_id varchar
);

CREATE TABLE IF NOT EXISTS vertex_ndl_ingest_cursor (
  vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
  provider_id varchar NOT NULL,
  query varchar NOT NULL,
  next_start_record bigint NOT NULL,
  last_run_id varchar,
  status varchar NOT NULL,
  updated_at varchar,
  org_id varchar, user_id varchar, actor_id varchar
);

CREATE TABLE IF NOT EXISTS vertex_ndl_ingest_run (
  vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
  run_id varchar NOT NULL,
  provider_id varchar NOT NULL,
  query varchar NOT NULL,
  start_record bigint,
  max_records int,
  max_items int,
  max_pages_per_item int,
  items_seen int,
  items_inserted int,
  pages_inserted int,
  pages_processed int,
  ocr_inserted int,
  bytes_webp bigint,
  status varchar NOT NULL,
  error varchar,
  started_at varchar,
  finished_at varchar,
  org_id varchar, user_id varchar, actor_id varchar
);
