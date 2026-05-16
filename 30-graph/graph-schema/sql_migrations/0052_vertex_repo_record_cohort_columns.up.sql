ALTER TABLE "vertex_repo_record" ADD COLUMN "cohort_did" VARCHAR;

ALTER TABLE "vertex_repo_record" ADD COLUMN "evidence_hash" VARCHAR;

ALTER TABLE "vertex_repo_record" ADD COLUMN "signal_kind" VARCHAR;

ALTER TABLE "vertex_repo_record" ADD COLUMN "posterior" DOUBLE PRECISION;

ALTER TABLE "vertex_repo_record" ADD COLUMN "judge_agreement" BOOLEAN;

ALTER TABLE "vertex_repo_record" ADD COLUMN "tier" VARCHAR;

ALTER TABLE "vertex_repo_record" ADD COLUMN "observed_at" VARCHAR;
