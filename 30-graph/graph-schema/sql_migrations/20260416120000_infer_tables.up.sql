CREATE TABLE IF NOT EXISTS "vertex_infer_input" (
    "vertex_id"       VARCHAR PRIMARY KEY,
    "_seq"            BIGINT,
    "created_date"    DATE,
    "sensitivity_ord" BIGINT,
    "owner_did"       VARCHAR,
    "source_type"     VARCHAR NOT NULL,
    "source_file"     VARCHAR,
    "features"        VARCHAR NOT NULL,
    "feature_names"   VARCHAR,
    "label"           VARCHAR,
    "batch_id"        VARCHAR NOT NULL
  );

CREATE INDEX IF NOT EXISTS "idx_vertex_infer_input_batch"
    ON "vertex_infer_input"("batch_id");

CREATE TABLE IF NOT EXISTS "vertex_infer_cluster" (
    "vertex_id"       VARCHAR PRIMARY KEY,
    "_seq"            BIGINT,
    "created_date"    DATE,
    "sensitivity_ord" BIGINT,
    "owner_did"       VARCHAR,
    "cluster_id"      BIGINT NOT NULL,
    "batch_id"        VARCHAR NOT NULL,
    "method"          VARCHAR NOT NULL,
    "centroid"        VARCHAR,
    "k_anonymity"     BIGINT,
    "member_count"    BIGINT,
    "segment_hash"    VARCHAR,
    "features_avg"    VARCHAR,
    "status"          VARCHAR DEFAULT 'active'
  );

CREATE INDEX IF NOT EXISTS "idx_vertex_infer_cluster_batch"
    ON "vertex_infer_cluster"("batch_id");

CREATE TABLE IF NOT EXISTS "vertex_infer_match" (
    "vertex_id"        VARCHAR PRIMARY KEY,
    "_seq"             BIGINT,
    "created_date"     DATE,
    "sensitivity_ord"  BIGINT,
    "owner_did"        VARCHAR,
    "cluster_id"       VARCHAR NOT NULL,
    "cohort_did"       VARCHAR NOT NULL,
    "similarity"       DOUBLE PRECISION NOT NULL,
    "posterior"         DOUBLE PRECISION,
    "match_method"     VARCHAR NOT NULL,
    "batch_id"         VARCHAR NOT NULL,
    "status"           VARCHAR DEFAULT 'candidate'
  );

CREATE INDEX IF NOT EXISTS "idx_vertex_infer_match_cohort"
    ON "vertex_infer_match"("cohort_did");

CREATE MATERIALIZED VIEW IF NOT EXISTS "mv_infer_cluster_summary" AS
    SELECT
      batch_id,
      label AS cluster_label,
      COUNT(*)::BIGINT AS input_count
    FROM "vertex_infer_input"
    WHERE batch_id IS NOT NULL AND label IS NOT NULL
    GROUP BY batch_id, label;
