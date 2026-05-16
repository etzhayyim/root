ALTER TABLE "vertex_profile_fragment"
    DROP COLUMN IF EXISTS "ivf_cluster_id";

ALTER TABLE "vertex_profile_fragment"
    DROP COLUMN IF EXISTS "embedding_norm";

ALTER TABLE "vertex_profile_fragment"
    DROP COLUMN IF EXISTS "embedding";
