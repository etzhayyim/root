CREATE TABLE IF NOT EXISTS vertex_isbn_book_image (
      vertex_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      isbn13 varchar NOT NULL,
      role varchar NOT NULL,
      page_index int,
      sha256 varchar NOT NULL,
      cid_v1 varchar,
      b2_bucket varchar,
      b2_key varchar,
      source varchar NOT NULL,
      source_url varchar,
      mime_type varchar,
      width_px int,
      height_px int,
      byte_size bigint,
      license varchar,
      status varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE TABLE IF NOT EXISTS edge_isbn_book_image (
      edge_id varchar PRIMARY KEY, _seq bigint, created_date date, sensitivity_ord int, owner_did varchar,
      src_vid varchar NOT NULL, dst_vid varchar NOT NULL, role varchar NOT NULL,
      created_at varchar, org_id varchar, user_id varchar, actor_id varchar);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_isbn_book_image_coverage AS
      SELECT
        source,
        role,
        COUNT(*) AS image_count,
        SUM(byte_size) AS total_bytes
      FROM vertex_isbn_book_image
      WHERE status='active'
      GROUP BY source, role;
