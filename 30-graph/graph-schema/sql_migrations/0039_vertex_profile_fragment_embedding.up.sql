ALTER TABLE "vertex_profile_fragment"
    ADD COLUMN IF NOT EXISTS "embedding" REAL[];

ALTER TABLE "vertex_profile_fragment"
    ADD COLUMN IF NOT EXISTS "embedding_norm" DOUBLE PRECISION;

ALTER TABLE "vertex_profile_fragment"
    ADD COLUMN IF NOT EXISTS "ivf_cluster_id" BIGINT;
