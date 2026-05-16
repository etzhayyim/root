import { Kysely, sql } from 'kysely';

/**
 * Migration 0006: typed columns added while archiving the SQL transpiler.
 *
 * Replaces former `props JSON` stuffing on a handful of vertex tables with
 * dedicated typed columns. Driven by the 2026-04-13 "no props, proper vertex
 * design" directive — see `deps.toml [[migrations]] sql-archive`.
 *
 * New columns:
 *   vertex_policy
 *     + rules_json TEXT        — policy rules payload (previously packed into props)
 *     + updated_at VARCHAR(64)
 *   vertex_convo
 *     + encryption VARCHAR(32) — "signal" | "plaintext"
 *     + updated_at VARCHAR(64)
 *   vertex_openclaw_connection
 *     + gateway_url VARCHAR(2048)
 *     + dashboard_url VARCHAR(2048)
 *     + connected_at VARCHAR(64)
 *     + updated_at VARCHAR(64)
 *   vertex_signaldevice
 *     + updated_at VARCHAR(64)
 *   vertex_did
 *     + doc TEXT               — already queried; make it a declared column
 *     + updated_at VARCHAR(64)
 *   vertex_did_document
 *     + updated_at VARCHAR(64)
 *   vertex_agent_key
 *     + updated_at VARCHAR(64)
 *   vertex_follow_request
 *     + updated_at VARCHAR(64)
 *   vertex_app
 *     + updated_at VARCHAR(64)
 *   vertex_esim_profile (new table; previously a virtual SQL label)
 *     — created here so the Telnyx eSIM handler has a typed target.
 *
 * The matching Row interfaces live in `src/database.ts` (snake_case, as of
 * 2026-04-13). `as any` on Kysely call sites is a blocker — all new edits
 * must type-check against the Database generic.
 */
export async function up(db: Kysely<any>): Promise<void> {
  // vertex_policy: rules_json + updated_at
  await db.executeQuery(sql`ALTER TABLE "vertex_policy" ADD COLUMN IF NOT EXISTS "rules_json" TEXT`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_policy" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64)`.compile(db));

  // vertex_convo: encryption + updated_at
  await db.executeQuery(sql`ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "encryption" VARCHAR(32)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64)`.compile(db));

  // vertex_openclaw_connection: gateway_url + dashboard_url + connected_at + updated_at
  await db.executeQuery(sql`ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "gateway_url" VARCHAR(2048)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "dashboard_url" VARCHAR(2048)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "connected_at" VARCHAR(64)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64)`.compile(db));

  // NOTE: vertex_repo_record / vertex_repo_root are created in migration 0007
  // (concurrent work — aligned with AT Protocol reference schema). Do not
  // duplicate the DDL here.

  // vertex_signaldevice: updated_at
  await db.executeQuery(sql`ALTER TABLE "vertex_signal_device" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64)`.compile(db));

  // vertex_form_task: updated_at (for form submission timestamp)
  await db.executeQuery(sql`ALTER TABLE "vertex_form_task" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64)`.compile(db));

  // ── OCEL 2.0 proper decomposition (no JSON catch-all) ──
  //
  // vertex_ocel_event carries only the scalar event fields. event→object links
  // become edge rows, and event attributes become one row per (event_id, name)
  // in vertex_ocel_event_attribute (EAV), which keeps the schema typed while
  // still tolerating OCEL's per-activity attribute flexibility.
  await db.executeQuery(sql`ALTER TABLE "vertex_ocel_event" ADD COLUMN IF NOT EXISTS "spec_version" VARCHAR(16)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_ocel_event" ADD COLUMN IF NOT EXISTS "timestamp" VARCHAR(64)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_ocel_event" ADD COLUMN IF NOT EXISTS "activity" VARCHAR(256)`.compile(db));

  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_ocel_object" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "object_id" VARCHAR(512),
    "object_type" VARCHAR(128),
    "updated_at" VARCHAR(64)
  )`.compile(db));

  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_ocel_event_object" (
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
  )`.compile(db));

  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_ocel_event_attribute" (
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
  )`.compile(db));

  // Agent memory tables (3-layer: short-term buffer, long-term summary, semantic facts).
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_agent_memory_short_term" (
    "memory_id" VARCHAR(512) PRIMARY KEY,
    "caller_did" VARCHAR(512),
    "session_id" VARCHAR(128),
    "seq" BIGINT,
    "role" VARCHAR(32),
    "content" TEXT,
    "tool_calls" TEXT,
    "created_at" VARCHAR(64)
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_agent_memory_long_term" (
    "memory_id" VARCHAR(512) PRIMARY KEY,
    "caller_did" VARCHAR(512),
    "summary" TEXT,
    "keywords" TEXT,
    "source_session" VARCHAR(128),
    "created_at" VARCHAR(64)
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_agent_memory_semantic" (
    "memory_id" VARCHAR(512) PRIMARY KEY,
    "caller_did" VARCHAR(512),
    "category" VARCHAR(128),
    "data" TEXT,
    "updated_at" VARCHAR(64)
  )`.compile(db));

  // vertex_did: updated_at
  await db.executeQuery(sql`ALTER TABLE "vertex_did" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64)`.compile(db));

  // vertex_did_document (created if missing) + updated_at
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_did_document" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "did" VARCHAR(512),
    "doc" TEXT,
    "updated_at" VARCHAR(64)
  )`.compile(db));

  // vertex_agent_key (created if missing)
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_agent_key" (
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
  )`.compile(db));

  // vertex_follow_request (created if missing)
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_follow_request" (
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
  )`.compile(db));

  // vertex_app: updated_at (no props — app carries only typed columns)
  await db.executeQuery(sql`ALTER TABLE "vertex_app" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64)`.compile(db));

  // vertex_esim_profile (new table for Telnyx eSIM writes)
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_esim_profile" (
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
  )`.compile(db));

  // ── OCEL 2.0 proper decomposition (no JSON catch-all) ──
  await db.executeQuery(sql`ALTER TABLE "vertex_ocel_event" ADD COLUMN IF NOT EXISTS "spec_version" VARCHAR(16)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_ocel_event" ADD COLUMN IF NOT EXISTS "timestamp" VARCHAR(64)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_ocel_event" ADD COLUMN IF NOT EXISTS "activity" VARCHAR(256)`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_ocel_object" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "object_id" VARCHAR(512),
    "object_type" VARCHAR(128),
    "updated_at" VARCHAR(64)
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "edge_ocel_event_object" (
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
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_ocel_event_attribute" (
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
  )`.compile(db));

  // ── ActorManifest decomposition (no JSON catch-all) ──
  // capabilities[]  → vertex_actor_capability (actor_did, capability) PK
  // triggers[]      → vertex_actor_pipeline_trigger
  // pipelines[]     → vertex_actor_pipeline + vertex_actor_pipeline_step (+ step args EAV)
  // profile         → vertex_actor_profile_meta
  // governance      → vertex_actor_governance
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_capability" (
    "vertex_id" VARCHAR(1024) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "actor_did" VARCHAR(512),
    "capability" VARCHAR(128),
    "status" VARCHAR(32)
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_pipeline" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "actor_did" VARCHAR(512),
    "pipeline_index" BIGINT,
    "status" VARCHAR(32)
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_pipeline_trigger" (
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
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_pipeline_step" (
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
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_pipeline_step_arg" (
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
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_profile_meta" (
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
  )`.compile(db));
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_actor_governance" (
    "vertex_id" VARCHAR(512) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "actor_did" VARCHAR(512),
    "classification" VARCHAR(64),
    "retention" VARCHAR(64),
    "visibility" VARCHAR(64)
  )`.compile(db));

  // ── BPMN element extensions EAV (no extensions_json) ──
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_bpmn_extension" (
    "vertex_id" VARCHAR(1024) PRIMARY KEY,
    "_seq" BIGINT,
    "created_date" DATE,
    "sensitivity_ord" BIGINT,
    "owner_did" VARCHAR(512),
    "element_did" VARCHAR(512),
    "key" VARCHAR(128),
    "value" TEXT
  )`.compile(db));

  // ── Form submission EAV (no variable_mappings_json) ──
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_form_submission_var" (
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
  )`.compile(db));

  // ── Form schema components (no components_json) ──
  await db.executeQuery(sql`CREATE TABLE IF NOT EXISTS "vertex_form_component" (
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
  )`.compile(db));
}

export async function down(_db: Kysely<any>): Promise<void> {
  // Non-destructive forward-only migration. Reverts require coordinated
  // data removal; leave `down` as a no-op per project convention.
}
