ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "kind" VARCHAR(64);

ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "depth" BIGINT;

ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "email" VARCHAR(512);

ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "description" TEXT;

ALTER TABLE "vertex_project_props" ADD COLUMN IF NOT EXISTS "priority" VARCHAR(32);

ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "kind" VARCHAR(64);

ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "members_json" TEXT;
