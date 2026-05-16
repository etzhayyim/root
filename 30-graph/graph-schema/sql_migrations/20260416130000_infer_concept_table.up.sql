CREATE TABLE IF NOT EXISTS "vertex_infer_concept" (
    "vertex_id"       VARCHAR PRIMARY KEY,
    "_seq"            BIGINT,
    "created_date"    DATE,
    "sensitivity_ord" BIGINT,
    "owner_did"       VARCHAR,
    "slug"            VARCHAR NOT NULL,
    "category"        VARCHAR NOT NULL,
    "display_name"    VARCHAR,
    "description"     VARCHAR,
    "era"             VARCHAR,
    "origin_country"  VARCHAR
  );

CREATE INDEX IF NOT EXISTS "idx_vertex_infer_concept_slug"
    ON "vertex_infer_concept"("slug");

CREATE INDEX IF NOT EXISTS "idx_vertex_infer_concept_category"
    ON "vertex_infer_concept"("category");
