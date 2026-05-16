-- Add contact and address fields to vertex_gov_org

ALTER TABLE "vertex_gov_org" ADD COLUMN IF NOT EXISTS "address" VARCHAR(1024);
ALTER TABLE "vertex_gov_org" ADD COLUMN IF NOT EXISTS "phone" VARCHAR(256);
ALTER TABLE "vertex_gov_org" ADD COLUMN IF NOT EXISTS "email" VARCHAR(512);
