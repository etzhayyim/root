import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2604291800 Well-Becoming Spirit Objective Function — process mining tables.
// OCEL 2.0 event log for per-agentInfer Well-Becoming evaluation.
// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── OCEL event log ──────────────────────────────────────────────────────
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_wellbecoming_event (
      vertex_id     VARCHAR PRIMARY KEY,
      _seq          BIGINT,
      created_date  DATE,

      -- OCEL 2.0 identifiers
      case_id       VARCHAR NOT NULL,   -- callerDid (conversation thread)
      agent_did     VARCHAR NOT NULL,   -- actor responding

      -- Activity (lexicographic layer that was most exercised)
      activity      VARCHAR NOT NULL,   -- 'infer_complete' | 'floor_check' | 'tool_blocked'
      layer_trigger VARCHAR,            -- 'spirit' | 'wellbecoming' | 'feeling' | 'buffer'

      -- Objective function scores (0.0–1.0, NULL = not yet scored by BPMN worker)
      score_spirit       DOUBLE PRECISION,
      score_wellbecoming DOUBLE PRECISION,
      score_feeling      DOUBLE PRECISION,
      score_buffer       DOUBLE PRECISION,
      score_total        DOUBLE PRECISION,  -- product: spirit × wellbecoming × feeling × buffer

      -- Minimax floor
      floor_violated BOOLEAN DEFAULT false,
      floor_reason   VARCHAR,

      -- Separation delta: positive = more connected, negative = more isolated
      -- Heuristic: LLM-assigned after the fact by processMining BPMN worker
      separation_delta DOUBLE PRECISION,

      -- Context snapshot
      response_length  BIGINT,
      tool_count       BIGINT,
      model            VARCHAR,
      response_preview VARCHAR,   -- first 300 chars for LLM scorer

      -- Lifecycle
      scored      BOOLEAN DEFAULT false,
      scored_at   TIMESTAMP,
      created_at  TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wbe_case
      ON vertex_wellbecoming_event (case_id)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wbe_agent
      ON vertex_wellbecoming_event (agent_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wbe_scored
      ON vertex_wellbecoming_event (scored, created_at)
  `.execute(db);

  // ── Actor-level rolling score MV ────────────────────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wellbecoming_score_actor AS
    SELECT
      agent_did,
      COUNT(*)                                                       AS event_count,
      AVG(score_spirit)       FILTER (WHERE scored = true)           AS avg_spirit,
      AVG(score_wellbecoming) FILTER (WHERE scored = true)           AS avg_wellbecoming,
      AVG(score_feeling)      FILTER (WHERE scored = true)           AS avg_feeling,
      AVG(score_buffer)       FILTER (WHERE scored = true)           AS avg_buffer,
      AVG(score_total)        FILTER (WHERE scored = true)           AS avg_total,
      SUM(CASE WHEN floor_violated = true THEN 1 ELSE 0 END)         AS floor_violations,
      AVG(separation_delta)   FILTER (WHERE separation_delta IS NOT NULL) AS avg_separation_delta,
      MAX(created_at)                                                AS last_activity_at
    FROM vertex_wellbecoming_event
    GROUP BY agent_did
  `.execute(db);

  // ── Hourly entropy trend MV ──────────────────────────────────────────────
  // Shannon η proxy: avg_separation_delta approaches 0 when connections degrade.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wellbecoming_entropy_trend AS
    SELECT
      date_trunc('hour', created_at)                                  AS hour,
      AVG(separation_delta) FILTER (WHERE separation_delta IS NOT NULL) AS avg_separation_delta,
      COUNT(*)                                                         AS event_count,
      COUNT(DISTINCT case_id)                                          AS active_conversations,
      SUM(CASE WHEN floor_violated = true THEN 1 ELSE 0 END)          AS floor_violations,
      AVG(score_total) FILTER (WHERE scored = true)                    AS avg_score_total
    FROM vertex_wellbecoming_event
    GROUP BY date_trunc('hour', created_at)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_wellbecoming_entropy_trend`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_wellbecoming_score_actor`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_wellbecoming_event`.execute(db);
}
