ALTER TABLE "vertex_actor" ADD COLUMN IF NOT EXISTS "val" TEXT;

ALTER TABLE "vertex_actor_manifest" ADD COLUMN IF NOT EXISTS "val" TEXT;
