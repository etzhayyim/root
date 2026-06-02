import type { Kysely } from "kysely";
import { sql } from "kysely";

const ownerDid = "did:web:magatama.etzhayyim.com";
const nsid = "com.etzhayyim.apps.magatama.organizerRun";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_magatama_organizer_run (
      vertex_id VARCHAR PRIMARY KEY,
      record_key VARCHAR NOT NULL,
      status VARCHAR NOT NULL,
      value_json TEXT NOT NULL,
      indexed_at VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      actor_did VARCHAR NOT NULL,
      org_did VARCHAR NOT NULL,
      owner_did VARCHAR NOT NULL,
      sensitivity_ord INTEGER NOT NULL DEFAULT 2,
      http_status INTEGER NOT NULL DEFAULT 0,
      runs_total_24h INTEGER NOT NULL DEFAULT 0,
      summary_hot INTEGER NOT NULL DEFAULT 0,
      summary_normal INTEGER NOT NULL DEFAULT 0,
      summary_stale INTEGER NOT NULL DEFAULT 0,
      summary_silent INTEGER NOT NULL DEFAULT 0,
      summary_archived INTEGER NOT NULL DEFAULT 0,
      fleet_saturation DOUBLE PRECISION NOT NULL DEFAULT 0,
      plan_ts VARCHAR,
      latency_ms INTEGER NOT NULL DEFAULT 0,
      error TEXT
    )
  `.execute(db);

  const oldTable = await sql<{ exists: boolean }>`
    SELECT EXISTS (
      SELECT 1 FROM information_schema.tables
      WHERE table_schema = current_schema()
        AND table_name = 'vertex_magatama_record'
    ) AS exists
  `.execute(db);

  if (oldTable.rows[0]?.exists) {
    await sql`
      INSERT INTO vertex_magatama_organizer_run (
        vertex_id, record_key, status, value_json, indexed_at, created_at,
        updated_at, actor_did, org_did, owner_did, sensitivity_ord,
        http_status, runs_total_24h, summary_hot, summary_normal,
        summary_stale, summary_silent, summary_archived, fleet_saturation,
        plan_ts, latency_ms, error
      )
      SELECT
        vertex_id,
        record_key,
        status,
        value_json,
        indexed_at,
        created_at,
        updated_at,
        actor_did,
        org_did,
        owner_did,
        CAST(sensitivity_ord AS integer),
        COALESCE((value_json::jsonb ->> 'httpStatus')::integer, 0),
        COALESCE((value_json::jsonb ->> 'runsTotal24h')::integer, 0),
        COALESCE((value_json::jsonb #>> '{summary,hot}')::integer, 0),
        COALESCE((value_json::jsonb #>> '{summary,normal}')::integer, 0),
        COALESCE((value_json::jsonb #>> '{summary,stale}')::integer, 0),
        COALESCE((value_json::jsonb #>> '{summary,silent}')::integer, 0),
        COALESCE((value_json::jsonb #>> '{summary,archived}')::integer, 0),
        COALESCE((value_json::jsonb ->> 'fleetSaturation')::double precision, 0),
        value_json::jsonb ->> 'planTs',
        COALESCE((value_json::jsonb ->> 'latencyMs')::integer, 0),
        value_json::jsonb ->> 'error'
      FROM vertex_magatama_record
      WHERE record_kind = 'organizerRun'
      ON CONFLICT (vertex_id) DO NOTHING
    `.execute(db);
  }

  await sql`
    CREATE INDEX IF NOT EXISTS idx_magatama_organizer_run_status_time
      ON vertex_magatama_organizer_run (status, indexed_at DESC)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_magatama_organizer_run_http_time
      ON vertex_magatama_organizer_run (http_status, indexed_at DESC)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_magatama_organizer_run_health AS
    SELECT
      status,
      COUNT(*) AS run_count,
      MAX(indexed_at) AS latest_indexed_at,
      AVG(fleet_saturation) AS avg_fleet_saturation,
      AVG(latency_ms) AS avg_latency_ms
    FROM vertex_magatama_organizer_run
    GROUP BY status
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = 'vertex_magatama_organizer_run'
    WHERE owner_did = ${ownerDid}
      AND nsid = ${nsid}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = ''
    WHERE owner_did = ${ownerDid}
      AND nsid = ${nsid}
  `.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_magatama_organizer_run_health`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_magatama_organizer_run`.execute(db);
}
