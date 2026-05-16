ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "cohort_did";

ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "evidence_hash";

ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "signal_kind";

ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "posterior";

ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "judge_agreement";

ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "tier";

ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "observed_at";
