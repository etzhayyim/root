CREATE TABLE IF NOT EXISTS "vertex_cohort_actor" (
    "vertex_id"       VARCHAR PRIMARY KEY,
    "cohort_did"      VARCHAR NOT NULL,
    "handle"          VARCHAR,
    "kind"            VARCHAR NOT NULL,
    "segment_hash"    VARCHAR NOT NULL,
    "k_anonymity"     BIGINT       NOT NULL,
    "fission_enabled" BOOLEAN      NOT NULL DEFAULT FALSE,
    "derived_from"    VARCHAR,
    "status"          VARCHAR NOT NULL,
    "signature_uri"   VARCHAR,
    "genesis_at"      VARCHAR NOT NULL,
    "owner_did"       VARCHAR,
    "_seq"            BIGINT,
    "created_date"    DATE
  );

CREATE INDEX IF NOT EXISTS "idx_vertex_cohort_actor_did" ON "vertex_cohort_actor"("cohort_did");

CREATE INDEX IF NOT EXISTS "idx_vertex_cohort_actor_derived_from" ON "vertex_cohort_actor"("derived_from");
