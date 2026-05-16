CREATE TABLE IF NOT EXISTS "vertex_repo_commit" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "seq" BIGINT,
    "repo" VARCHAR(512),
    "collection" VARCHAR(512),
    "rkey" VARCHAR(64),
    "action" VARCHAR(16),
    "rev" VARCHAR(64),
    "cid" VARCHAR(512),
    "prev" VARCHAR(512),
    "sig" TEXT,
    "value_json" TEXT,
    "ts_ms" BIGINT,
    "record_cid" VARCHAR(512),
    "created_at" VARCHAR(64)
  );

CREATE TABLE IF NOT EXISTS "vertex_repo_block" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "cid" VARCHAR(512),
    "repo" VARCHAR(512),
    "content" TEXT,
    "size_bytes" BIGINT,
    "created_at" VARCHAR(64)
  );

CREATE TABLE IF NOT EXISTS "vertex_consumer_cursor" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "consumer_id" VARCHAR(256),
    "last_seq" BIGINT,
    "updated_at" VARCHAR(64)
  );
