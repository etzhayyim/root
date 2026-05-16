-- Remove contact and address fields from vertex_gov_org

ALTER TABLE "vertex_gov_org" DROP COLUMN IF EXISTS "address";
ALTER TABLE "vertex_gov_org" DROP COLUMN IF EXISTS "phone";
ALTER TABLE "vertex_gov_org" DROP COLUMN IF EXISTS "email";
