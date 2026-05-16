CREATE TABLE IF NOT EXISTS "vertex_gitrepo" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "name" VARCHAR(256),
    "nanoid" VARCHAR(64),
    "template" VARCHAR(128),
    "head_sha" VARCHAR(64),
    "head_ref" VARCHAR(256),
    "org_id" VARCHAR(64),
    "user_id" VARCHAR(64),
    "actor_id" VARCHAR(64),
    "updated_at" VARCHAR(64)
  );
