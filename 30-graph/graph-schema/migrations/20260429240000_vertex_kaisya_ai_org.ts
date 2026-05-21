import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2604291800 Artificial Organism — etzhayyim AI agent org P1
// tier: C
// vertex_kaisya_task: human approval tasklist (sole human-facing interface)
// vertex_kaisya_agent_run: agent execution log (audit trail per timer-start)
// mv_kaisya_pending_count: per-human pending task count (8 distinct human_did values)

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Human approval tasklist ─────────────────────────────────────────────
  // Populated by BPMN workers when a decision requires human gate.
  // kaisya.etzhayyim.com/tasks UI reads this; humans approve/reject via XRPC.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaisya_task (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_id         VARCHAR NOT NULL,   -- kaisya_ceo_agent etc.
      human_did        VARCHAR NOT NULL,   -- responsible approver DID
      title            VARCHAR NOT NULL,
      context_json     VARCHAR,            -- JSON blob (task details, links)
      priority         INTEGER DEFAULT 2,  -- 1=critical 2=normal 3=low
      status           VARCHAR NOT NULL DEFAULT 'pending',
      -- 'pending' | 'approved' | 'rejected' | 'expired'
      due_at           TIMESTAMP,
      resolved_at      TIMESTAMP,
      resolved_by      VARCHAR,
      resolution_note  VARCHAR,

      -- RLS 3-col
      owner_did        VARCHAR NOT NULL,
      org_id           VARCHAR NOT NULL,
      user_id          VARCHAR NOT NULL,

      sensitivity_ord  INTEGER NOT NULL DEFAULT 1,
      actor_id         VARCHAR,
      created_at       TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kaisya_task_human
      ON vertex_kaisya_task (human_did, status, created_at)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kaisya_task_agent
      ON vertex_kaisya_task (agent_id, status)
  `.execute(db);

  // ── Agent execution log ─────────────────────────────────────────────────
  // One row per timer-start BPMN process instance completion.
  // CEO/CLO/COO/Eng agents write here after each cadence run.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kaisya_agent_run (
      vertex_id        VARCHAR PRIMARY KEY,
      agent_id         VARCHAR NOT NULL,   -- kaisya_ceo_agent etc.
      process_id       VARCHAR NOT NULL,   -- BPMN processId
      task_type        VARCHAR NOT NULL,   -- dailyBriefing / deployHealthCheck etc.
      human_did        VARCHAR NOT NULL,   -- associated human
      status           VARCHAR NOT NULL DEFAULT 'ok',
      -- 'ok' | 'partial' | 'error'
      output_summary   VARCHAR,
      tasks_created    BIGINT DEFAULT 0,
      ran_at           TIMESTAMP NOT NULL,

      -- RLS 3-col
      owner_did        VARCHAR NOT NULL,
      org_id           VARCHAR NOT NULL,
      user_id          VARCHAR NOT NULL,

      sensitivity_ord  INTEGER NOT NULL DEFAULT 1,
      actor_id         VARCHAR,
      created_at       TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kaisya_run_agent
      ON vertex_kaisya_agent_run (agent_id, ran_at)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_kaisya_run_human
      ON vertex_kaisya_agent_run (human_did, ran_at)
  `.execute(db);

  // ── Pending task count MV (8 distinct human_did values — safe for streaming MV) ─
  // Refreshed automatically by RisingWave streaming (<100ms freshness).
  // Used by kaisya.etzhayyim.com/tasks badge + Teams push notification threshold.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kaisya_pending_count AS
    SELECT
      human_did,
      COUNT(*)                                    AS pending_count,
      COUNT(*) FILTER (WHERE priority = 1)        AS critical_count,
      MIN(due_at)                                 AS earliest_due_at,
      MAX(created_at)                             AS latest_task_at
    FROM vertex_kaisya_task
    WHERE status = 'pending'
    GROUP BY human_did
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kaisya_pending_count`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kaisya_agent_run`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kaisya_task`.execute(db);
}
