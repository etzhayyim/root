ALTER TABLE "vertex_capability" ADD COLUMN IF NOT EXISTS "input_schema_json" TEXT;

ALTER TABLE "vertex_capability" ADD COLUMN IF NOT EXISTS "tags" TEXT;

ALTER TABLE "vertex_capability" ADD COLUMN IF NOT EXISTS "capability_worker" VARCHAR(512);

ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "encryption" VARCHAR(32);

ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64);

ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "gateway_url" VARCHAR(512);

ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "dashboard_url" VARCHAR(512);

ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "connected_at" VARCHAR(64);

ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64);

ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "status" VARCHAR(32);

ALTER TABLE "vertex_ocel_event" ADD COLUMN IF NOT EXISTS "spec_version" VARCHAR(16);

ALTER TABLE "vertex_ocel_event" ADD COLUMN IF NOT EXISTS "timestamp" VARCHAR(64);

ALTER TABLE "vertex_ocel_event" ADD COLUMN IF NOT EXISTS "activity" VARCHAR(256);

CREATE TABLE IF NOT EXISTS "vertex_ocel_object" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "object_id" VARCHAR(512),
    "object_type" VARCHAR(128),
    "updated_at" VARCHAR(64)
  );

CREATE TABLE IF NOT EXISTS "edge_ocel_event_object" (
    "edge_id" VARCHAR(1024) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "label" VARCHAR(64),
    "src_vid" VARCHAR(512),
    "dst_vid" VARCHAR(512),
    "event_id" VARCHAR(512),
    "object_id" VARCHAR(512),
    "object_type" VARCHAR(128),
    "qualifier" VARCHAR(128)
  );

CREATE TABLE IF NOT EXISTS "vertex_ocel_event_attribute" (
    "vertex_id" VARCHAR(1024) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "event_id" VARCHAR(512),
    "name" VARCHAR(128),
    "value_text" TEXT,
    "value_num" DOUBLE PRECISION,
    "value_ts" VARCHAR(64)
  );
