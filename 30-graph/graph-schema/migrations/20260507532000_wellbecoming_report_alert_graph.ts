import type { Kysely } from "kysely";
import { sql } from "kysely";

const allowlist = [
  "vertex_wellbecoming_event",
  "vertex_actor_wellbecoming_profile",
  "vertex_wellbecoming_proactive_message",
  "vertex_wellbecoming_floor_alert",
  "vertex_wellbecoming_process_mining_report",
].join(",");

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wellbecoming_proactive_message (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      text TEXT NOT NULL,
      caller_did VARCHAR,
      bottleneck_axis VARCHAR,
      avg_separation_delta DOUBLE PRECISION,
      value_json TEXT NOT NULL,
      indexed_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wellbecoming_floor_alert (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      text TEXT NOT NULL,
      violation_count INTEGER NOT NULL DEFAULT 0,
      violation_ids_json TEXT,
      value_json TEXT NOT NULL,
      indexed_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wellbecoming_process_mining_report (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      text TEXT NOT NULL,
      scored_count INTEGER NOT NULL DEFAULT 0,
      floor_violations INTEGER NOT NULL DEFAULT 0,
      avg_spirit DOUBLE PRECISION,
      avg_separation_delta DOUBLE PRECISION,
      value_json TEXT NOT NULL,
      indexed_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2
    )
  `.execute(db);

  const oldTable = await sql<{ exists: boolean }>`
    SELECT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = current_schema()
        AND table_name = 'vertex_wellbecoming_record'
    ) AS exists
  `.execute(db);

  if (oldTable.rows[0]?.exists) {
    await sql`
      INSERT INTO vertex_wellbecoming_proactive_message (
        vertex_id, record_key, text, caller_did, bottleneck_axis,
        avg_separation_delta, value_json, indexed_at, created_at, updated_at,
        actor_did, org_did, owner_did, sensitivity_ord
      )
      SELECT
        vertex_id,
        record_key,
        COALESCE(value_json::jsonb ->> 'text', label, ''),
        value_json::jsonb ->> 'callerDid',
        value_json::jsonb ->> 'bottleneckAxis',
        COALESCE((value_json::jsonb ->> 'avgSeparationDelta')::double precision, 0),
        value_json,
        indexed_at,
        created_at,
        updated_at,
        actor_did,
        org_did,
        owner_did,
        CAST(sensitivity_ord AS integer)
      FROM vertex_wellbecoming_record
      WHERE record_kind = 'app.etzhayyim.apps.wellbecoming.proactiveMessage'
      ON CONFLICT (vertex_id) DO NOTHING
    `.execute(db);

    await sql`
      INSERT INTO vertex_wellbecoming_floor_alert (
        vertex_id, record_key, text, violation_count, violation_ids_json,
        value_json, indexed_at, created_at, updated_at, actor_did, org_did,
        owner_did, sensitivity_ord
      )
      SELECT
        vertex_id,
        record_key,
        COALESCE(value_json::jsonb ->> 'text', label, ''),
        COALESCE((value_json::jsonb ->> 'violationCount')::integer, 0),
        COALESCE(value_json::jsonb -> 'violationIds', '[]'::jsonb)::text,
        value_json,
        indexed_at,
        created_at,
        updated_at,
        actor_did,
        org_did,
        owner_did,
        CAST(sensitivity_ord AS integer)
      FROM vertex_wellbecoming_record
      WHERE record_kind = 'app.etzhayyim.apps.wellbecoming.floorAlert'
      ON CONFLICT (vertex_id) DO NOTHING
    `.execute(db);

    await sql`
      INSERT INTO vertex_wellbecoming_process_mining_report (
        vertex_id, record_key, text, scored_count, floor_violations,
        avg_spirit, avg_separation_delta, value_json, indexed_at, created_at,
        updated_at, actor_did, org_did, owner_did, sensitivity_ord
      )
      SELECT
        vertex_id,
        record_key,
        COALESCE(value_json::jsonb ->> 'text', label, ''),
        COALESCE((value_json::jsonb ->> 'scoredCount')::integer, 0),
        COALESCE((value_json::jsonb ->> 'floorViolations')::integer, 0),
        (value_json::jsonb ->> 'avgSpirit')::double precision,
        (value_json::jsonb ->> 'avgSeparationDelta')::double precision,
        value_json,
        indexed_at,
        created_at,
        updated_at,
        actor_did,
        org_did,
        owner_did,
        CAST(sensitivity_ord AS integer)
      FROM vertex_wellbecoming_record
      WHERE record_kind = 'app.etzhayyim.apps.wellbecoming.processMiningReport'
      ON CONFLICT (vertex_id) DO NOTHING
    `.execute(db);
  }

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wb_proactive_message_caller_time
      ON vertex_wellbecoming_proactive_message (caller_did, indexed_at DESC)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wb_floor_alert_count_time
      ON vertex_wellbecoming_floor_alert (violation_count, indexed_at DESC)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wb_process_mining_report_time
      ON vertex_wellbecoming_process_mining_report (indexed_at DESC)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wellbecoming_report_health AS
    SELECT
      COUNT(*) AS report_count,
      SUM(scored_count) AS scored_count,
      SUM(floor_violations) AS floor_violations,
      AVG(avg_spirit) AS avg_spirit,
      AVG(avg_separation_delta) AS avg_separation_delta,
      MAX(indexed_at) AS latest_indexed_at
    FROM vertex_wellbecoming_process_mining_report
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wellbecoming_proactive_message_caller_counts AS
    SELECT caller_did, COUNT(*) AS message_count, MAX(indexed_at) AS latest_indexed_at
    FROM vertex_wellbecoming_proactive_message
    GROUP BY caller_did
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = ${allowlist}
    WHERE nsid IN (
      'app.etzhayyim.apps.wellbecoming.agentLoop',
      'app.etzhayyim.apps.wellbecoming.proactiveConnect',
      'app.etzhayyim.apps.wellbecoming.floorViolationAlert',
      'app.etzhayyim.apps.wellbecoming.processMining'
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_wellbecoming_proactive_message_caller_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_wellbecoming_report_health`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_wellbecoming_process_mining_report`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_wellbecoming_floor_alert`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_wellbecoming_proactive_message`.execute(db);
}
