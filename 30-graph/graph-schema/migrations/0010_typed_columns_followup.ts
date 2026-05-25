import { Kysely, sql } from 'kysely';

/**
 * Migration 0010 — follow-up typed columns to retire the last props JSON
 * catch-alls on vertex_capability, vertex_convo, vertex_openclaw_connection,
 * and vertex_ocel_event.
 *
 * Re-establishes the proper-decomposition work from the earlier 0008 draft
 * that was superseded by 0008_analytics_mvs (renamed upstream). Forward-only.
 *
 *   vertex_capability: input_schema_json / tags / capability_worker
 *     — MCP tool definitions registered via app.etzhayyim.tool.register.
 *   vertex_convo: encryption ("signal" | "plaintext"), updated_at
 *     — replaces props = {encryption, encryptionUpdatedAt}.
 *   vertex_openclaw_connection: gateway_url / dashboard_url / connected_at
 *     — replaces props = {ownerDid, gatewayUrl, dashboardUrl, connectedAt}.
 *   vertex_ocel_event: spec_version / timestamp / activity
 *     + vertex_ocel_object, edge_ocel_event_object, vertex_ocel_event_attribute
 *     — OCEL 2.0 decomposition (events, objects, event↔object edges, EAV attrs).
 */
export async function up(db: Kysely<any>): Promise<void> {
  // ── vertex_capability typed columns for MCP tool registry ──
  await db.executeQuery(sql`ALTER TABLE "vertex_capability" ADD COLUMN IF NOT EXISTS "input_schema_json" TEXT`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_capability" ADD COLUMN IF NOT EXISTS "tags" TEXT`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_capability" ADD COLUMN IF NOT EXISTS "capability_worker" VARCHAR(512)`.compile(db));

  // ── vertex_convo encryption mode ──
  await db.executeQuery(sql`ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "encryption" VARCHAR(32)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_convo" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64)`.compile(db));

  // ── vertex_openclaw_connection typed columns ──
  await db.executeQuery(sql`ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "gateway_url" VARCHAR(512)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "dashboard_url" VARCHAR(512)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "connected_at" VARCHAR(64)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "updated_at" VARCHAR(64)`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_openclaw_connection" ADD COLUMN IF NOT EXISTS "status" VARCHAR(32)`.compile(db));

  // ── OCEL 2.0 typed columns on the event vertex ──
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
}

export async function down(_db: Kysely<any>): Promise<void> {
  // Forward-only.
}
