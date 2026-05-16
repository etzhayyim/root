/**
 * ADR-0057 — mangaka pipeline process-mining MV.
 *
 * Projects `vertex_repo_commit` rows where `collection = 'ai.gftd.bpmn.audit'`
 * and the embedded action is `mangaka.*` into a flat OCEL 2.0 trace table
 * keyed by `case_id` (= episode AT URI / charSlug-ts string). Used by:
 *
 *   - ai.gftd.apps.mangaka.getProcessTrace XRPC query (per-episode timeline)
 *   - PM4PY / Celonis Iceberg export (cross-episode bottleneck analysis)
 *   - mangaka actor's /mcp `getProcessTrace` tool
 *
 * Primary key: (case_id, ts_ms). One mv row per audit emit.
 *
 * Why two MVs:
 *   - mv_mangaka_process_trace: per-event detail (the activity log itself)
 *   - mv_mangaka_process_kpi:   per-activity KPIs (count, avg/p95 duration,
 *                               error rate) — feeds dashboards / SLO alerts
 *
 * Both are RisingWave streaming MVs (sub-100ms freshness), so /getProcessTrace
 * returns up-to-the-second status while the BPMN process is still running.
 */

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  // Per-event trace
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mangaka_process_trace AS
    SELECT
      (value_json::jsonb -> 'case_id')::varchar    AS case_id,
      (value_json::jsonb -> 'action')::varchar     AS activity,
      repo                                         AS actor_did,
      ts_ms                                        AS ts_ms,
      created_at                                   AS timestamp,
      ((value_json::jsonb -> 'duration_ms')::varchar)::bigint   AS duration_ms,
      (value_json::jsonb -> 'status')::varchar     AS status,
      (value_json::jsonb -> 'objectRefs')::varchar AS object_refs_json,
      value_json                                   AS payload_json
    FROM vertex_repo_commit
    WHERE collection = 'ai.gftd.bpmn.audit'
      AND (value_json::jsonb -> 'action')::varchar LIKE 'mangaka.%'
  `.execute(db);

  // Per-activity KPI rollup (powers SLO + bottleneck visualization)
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mangaka_process_kpi AS
    SELECT
      activity,
      count(*)                                          AS exec_count,
      avg(duration_ms)::bigint                          AS avg_duration_ms,
      max(duration_ms)                                  AS max_duration_ms,
      min(duration_ms)                                  AS min_duration_ms,
      sum(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count,
      sum(CASE WHEN status = 'partial' THEN 1 ELSE 0 END) AS partial_count
    FROM mv_mangaka_process_trace
    WHERE duration_ms IS NOT NULL
    GROUP BY activity
  `.execute(db);

  // Per-case (episode) summary — used by getProcessTrace as `summary` field
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_mangaka_process_case_summary AS
    SELECT
      case_id,
      count(*)                                          AS phase_count,
      sum(duration_ms)                                  AS total_duration_ms,
      sum(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS error_count,
      max(timestamp)                                    AS last_event_at,
      CASE
        WHEN max(activity) = 'mangaka.episodePublished' THEN 'complete'
        WHEN sum(CASE WHEN status = 'error' THEN 1 ELSE 0 END) > 0 THEN 'failed'
        ELSE 'running'
      END                                               AS status
    FROM mv_mangaka_process_trace
    GROUP BY case_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_mangaka_process_case_summary`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_mangaka_process_kpi`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_mangaka_process_trace`.execute(db);
}
