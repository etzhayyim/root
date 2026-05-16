ALTER TABLE "vertex_policy" ADD COLUMN IF NOT EXISTS "rules_json" TEXT;

ALTER TABLE "vertex_policy" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64);

ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "encryption" VARCHAR(32);

ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64);

ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "gateway_url" VARCHAR(2048);

ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "dashboard_url" VARCHAR(2048);

ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "connected_at" VARCHAR(64);

ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64);

ALTER TABLE "vertex_signal_device" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64);

ALTER TABLE "vertex_form_task" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64);

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

CREATE TABLE IF NOT EXISTS "vertex_agent_memory_short_term" (
    "memory_id" VARCHAR(512) PRIMARY KEY,
    "caller_did" VARCHAR(512),
    "session_id" VARCHAR(128),
    "seq" BIGINT,
    "role" VARCHAR(32),
    "content" TEXT,
    "tool_calls" TEXT,
    "created_at" VARCHAR(64)
  );

CREATE TABLE IF NOT EXISTS "vertex_agent_memory_long_term" (
    "memory_id" VARCHAR(512) PRIMARY KEY,
    "caller_did" VARCHAR(512),
    "summary" TEXT,
    "keywords" TEXT,
    "source_session" VARCHAR(128),
    "created_at" VARCHAR(64)
  );

CREATE TABLE IF NOT EXISTS "vertex_agent_memory_semantic" (
    "memory_id" VARCHAR(512) PRIMARY KEY,
    "caller_did" VARCHAR(512),
    "category" VARCHAR(128),
    "data" TEXT,
    "updated_at" VARCHAR(64)
  );

ALTER TABLE "vertex_did" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64);

CREATE TABLE IF NOT EXISTS "vertex_did_document" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "did" VARCHAR(512),
    "doc" TEXT,
    "updated_at" VARCHAR(64)
  );

CREATE TABLE IF NOT EXISTS "vertex_agent_key" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "did" VARCHAR(512),
    "text" VARCHAR(512),
    "status" VARCHAR(64),
    "algorithm" VARCHAR(64),
    "public_key_multibase" VARCHAR(512),
    "key_id" VARCHAR(256),
    "updated_at" VARCHAR(64)
  );

CREATE TABLE IF NOT EXISTS "vertex_follow_request" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "rkey" VARCHAR(64),
    "repo" VARCHAR(512),
    "did" VARCHAR(512),
    "status" VARCHAR(64),
    "updated_at" VARCHAR(64)
  );

ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64);

CREATE TABLE IF NOT EXISTS "vertex_esim_profile" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "did" VARCHAR(512),
    "iccid" VARCHAR(64),
    "sim_card_id" VARCHAR(128),
    "user_id" VARCHAR(64),
    "org_id" VARCHAR(64),
    "actor_id" VARCHAR(64),
    "provider" VARCHAR(64),
    "coverage" VARCHAR(64),
    "data_plan" VARCHAR(64),
    "data_remaining_mb" BIGINT,
    "data_used_mb" BIGINT,
    "status" VARCHAR(64),
    "activation_code" VARCHAR(1024),
    "qr_code_url" VARCHAR(2048),
    "created_at" VARCHAR(64),
    "updated_at" VARCHAR(64)
  );

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

CREATE TABLE IF NOT EXISTS "vertex_actor_capability" (
    "vertex_id" VARCHAR(1024) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "actor_did" VARCHAR(512),
    "capability" VARCHAR(128),
    "status" VARCHAR(32)
  );

CREATE TABLE IF NOT EXISTS "vertex_actor_pipeline" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "actor_did" VARCHAR(512),
    "pipeline_index" BIGINT,
    "status" VARCHAR(32)
  );

CREATE TABLE IF NOT EXISTS "vertex_actor_pipeline_trigger" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "pipeline_id" VARCHAR(512),
    "trigger_type" VARCHAR(64),
    "cron" VARCHAR(128),
    "collections" TEXT,
    "nsid_pattern" VARCHAR(512)
  );

CREATE TABLE IF NOT EXISTS "vertex_actor_pipeline_step" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "pipeline_id" VARCHAR(512),
    "step_index" BIGINT,
    "step_id" VARCHAR(128),
    "fn" VARCHAR(128),
    "handler_src" TEXT,
    "capabilities" TEXT
  );

CREATE TABLE IF NOT EXISTS "vertex_actor_pipeline_step_arg" (
    "vertex_id" VARCHAR(1024) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "step_id" VARCHAR(512),
    "name" VARCHAR(128),
    "value_text" TEXT,
    "value_num" DOUBLE PRECISION,
    "value_bool" VARCHAR(8)
  );

CREATE TABLE IF NOT EXISTS "vertex_actor_profile_meta" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "actor_did" VARCHAR(512),
    "display_name" VARCHAR(1024),
    "description" TEXT,
    "avatar_cid" VARCHAR(512),
    "banner_cid" VARCHAR(512)
  );

CREATE TABLE IF NOT EXISTS "vertex_actor_governance" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "actor_did" VARCHAR(512),
    "classification" VARCHAR(64),
    "retention" VARCHAR(64),
    "visibility" VARCHAR(64)
  );

CREATE TABLE IF NOT EXISTS "vertex_bpmn_extension" (
    "vertex_id" VARCHAR(1024) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "element_did" VARCHAR(512),
    "key" VARCHAR(128),
    "value" TEXT
  );

CREATE TABLE IF NOT EXISTS "vertex_form_submission_var" (
    "vertex_id" VARCHAR(1024) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "form_task_id" VARCHAR(512),
    "name" VARCHAR(128),
    "value_text" TEXT,
    "value_num" DOUBLE PRECISION,
    "value_ts" VARCHAR(64),
    "value_bool" VARCHAR(8)
  );

CREATE TABLE IF NOT EXISTS "vertex_form_component" (
    "vertex_id" VARCHAR(1024) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "form_did" VARCHAR(512),
    "component_id" VARCHAR(128),
    "component_index" BIGINT,
    "type" VARCHAR(64),
    "label" VARCHAR(512),
    "required" VARCHAR(8),
    "placeholder" VARCHAR(512),
    "options" TEXT
  );
