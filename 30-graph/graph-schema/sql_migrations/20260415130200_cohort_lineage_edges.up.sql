CREATE TABLE IF NOT EXISTS "edge_cohort_derived" (
    "edge_id"      VARCHAR PRIMARY KEY,
    "src_vid"      VARCHAR NOT NULL,
    "dst_vid"      VARCHAR NOT NULL,
    "_seq"         BIGINT,
    "created_date" DATE,
    "owner_did"    VARCHAR,
    "posterior"    DOUBLE PRECISION,
    "fission_at"   VARCHAR
  );

CREATE INDEX IF NOT EXISTS "idx_edge_cohort_derived_src" ON "edge_cohort_derived"("src_vid");

CREATE INDEX IF NOT EXISTS "idx_edge_cohort_derived_dst" ON "edge_cohort_derived"("dst_vid");

CREATE TABLE IF NOT EXISTS "edge_cohort_evidence_about" (
    "edge_id"      VARCHAR PRIMARY KEY,
    "src_vid"      VARCHAR NOT NULL,
    "dst_vid"      VARCHAR NOT NULL,
    "_seq"         BIGINT,
    "created_date" DATE,
    "owner_did"    VARCHAR,
    "signal_kind"  VARCHAR,
    "posterior"    DOUBLE PRECISION,
    "observed_at"  VARCHAR
  );

CREATE INDEX IF NOT EXISTS "idx_edge_cohort_evidence_dst" ON "edge_cohort_evidence_about"("dst_vid");

CREATE TABLE IF NOT EXISTS "edge_cohort_routes_to" (
    "edge_id"      VARCHAR PRIMARY KEY,
    "src_vid"      VARCHAR NOT NULL,
    "dst_vid"      VARCHAR NOT NULL,
    "_seq"         BIGINT,
    "created_date" DATE,
    "owner_did"    VARCHAR,
    "pcf_l1"       VARCHAR,
    "registered_at" VARCHAR
  );

CREATE INDEX IF NOT EXISTS "idx_edge_cohort_routes_pcfl1" ON "edge_cohort_routes_to"("pcf_l1");

CREATE MATERIALIZED VIEW IF NOT EXISTS "mv_cohort_lineage_depth" AS
    SELECT
      src_vid AS cohort_did,
      COUNT(*)::BIGINT AS direct_children,
      MAX(fission_at) AS last_fission_at
    FROM "edge_cohort_derived"
    GROUP BY src_vid;
