CREATE TABLE IF NOT EXISTS vertex_hf_dataset (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      slug varchar NOT NULL,
      org varchar,
      name varchar,
      modality varchar,
      license varchar,
      hf_url varchar,
      task_categories varchar,
      tags varchar,
      row_count_expected bigint,
      row_count_ingested bigint,
      last_synced_at varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS vertex_hf_dataset_record (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      slug varchar NOT NULL,
      record_id varchar NOT NULL,
      split varchar,
      lang varchar,
      text_for_training varchar,
      text_byte_size int,
      raw_json varchar,
      source_uri varchar,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hf_dataset_text_for_training AS
      SELECT
        r.vertex_id                       AS vertex_id,
        'hf:' || r.slug                   AS label,
        r.text_for_training               AS content,
        r.lang                            AS lang,
        r.split                           AS split,
        CAST(r.created_date AS VARCHAR)   AS created_date
      FROM vertex_hf_dataset_record r
      WHERE r.sensitivity_ord = 0
        AND r.text_for_training IS NOT NULL
        AND r.text_for_training NOT LIKE 'signal:v1:%'
        AND LENGTH(r.text_for_training) >= 20;

GRANT SELECT, INSERT, UPDATE ON vertex_hf_dataset TO root;

GRANT SELECT, INSERT, UPDATE ON vertex_hf_dataset TO kaisya_app;

GRANT SELECT, INSERT ON vertex_hf_dataset_record TO root;

GRANT SELECT, INSERT ON vertex_hf_dataset_record TO kaisya_app;
