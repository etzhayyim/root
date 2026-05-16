import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-2604291800 Well-Becoming Spirit — per-caller profile + bottleneck MV.
// Foundations for LangGraph agent loop personalization and proactive connect.
// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Per-caller Well-Becoming profile ────────────────────────────────────
  // Upserted by wellbecoming.processMining.analyze after each scoring batch.
  // LangGraph load_profile node reads this for context injection.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_actor_wellbecoming_profile (
      vertex_id     VARCHAR PRIMARY KEY,
      actor_did     VARCHAR NOT NULL,  -- agent that responded
      caller_did    VARCHAR NOT NULL,  -- person being served

      -- Running averages (updated each processMining run)
      avg_spirit            DOUBLE PRECISION,
      avg_wellbecoming      DOUBLE PRECISION,
      avg_feeling           DOUBLE PRECISION,
      avg_buffer            DOUBLE PRECISION,
      avg_total             DOUBLE PRECISION,
      avg_separation_delta  DOUBLE PRECISION,

      -- Bottleneck: which U axis is lowest right now
      bottleneck_axis       VARCHAR,  -- 'spirit'|'wellbecoming'|'feeling'|'buffer'|null

      -- Trend over last 24h
      separation_trend      VARCHAR DEFAULT 'stable',  -- 'improving'|'stable'|'degrading'
      at_risk               BOOLEAN DEFAULT false,     -- separation_delta < -0.3

      -- Counts
      event_count           BIGINT DEFAULT 0,
      floor_violation_count BIGINT DEFAULT 0,

      -- Proactive connection tracking
      last_proactive_at     TIMESTAMP,
      proactive_count       BIGINT DEFAULT 0,

      -- Timestamps
      last_scored_at        TIMESTAMP,
      updated_at            TIMESTAMP,
      created_at            TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wbp_caller
      ON vertex_actor_wellbecoming_profile (caller_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_wbp_at_risk
      ON vertex_actor_wellbecoming_profile (at_risk, updated_at)
  `.execute(db);

  // ── Bottleneck MV per caller (last 24h scored events) ───────────────────
  // Streaming; Python query adds at_risk filter at runtime.
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wellbecoming_bottleneck_caller AS
    SELECT
      case_id                                                         AS caller_did,
      COUNT(*)                                                        AS event_count,
      AVG(score_spirit)       FILTER (WHERE scored = true)           AS avg_spirit,
      AVG(score_wellbecoming) FILTER (WHERE scored = true)           AS avg_wellbecoming,
      AVG(score_feeling)      FILTER (WHERE scored = true)           AS avg_feeling,
      AVG(score_buffer)       FILTER (WHERE scored = true)           AS avg_buffer,
      AVG(score_total)        FILTER (WHERE scored = true)           AS avg_total,
      AVG(separation_delta)   FILTER (WHERE separation_delta IS NOT NULL) AS avg_separation_delta,
      SUM(CASE WHEN floor_violated = true THEN 1 ELSE 0 END)         AS floor_violations,
      MAX(created_at)                                                 AS last_activity_at
    FROM vertex_wellbecoming_event
    GROUP BY case_id
  `.execute(db);

  // ── At-risk callers MV (separation_delta < -0.3) ─────────────────────────
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wellbecoming_at_risk AS
    SELECT
      caller_did,
      avg_separation_delta,
      avg_spirit,
      avg_total,
      floor_violations,
      last_activity_at
    FROM mv_wellbecoming_bottleneck_caller
    WHERE avg_separation_delta < -0.3
       OR floor_violations > 0
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_wellbecoming_at_risk`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_wellbecoming_bottleneck_caller`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_actor_wellbecoming_profile`.execute(db);
}
