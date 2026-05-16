import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0098 Repo-as-Attractor — ρ(J) < 1 のリアルタイム推定 MV.
// SBGE attractor 安定条件の代理指標を vertex_wellbecoming_event から streaming で計測する。
//
// 安定条件の実装対応:
//   STDDEV(score_total) → entropy spread の proxy
//   spread 収縮 → ρ(J) < 1 の近似証拠（beliefs converging）
//   spread 拡大 → ρ(J) → 1 の警告（beliefs diverging）
//
// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── mv_attractor_stability ───────────────────────────────────────────────
  // scored = true のイベント全体から信念収束度を streaming 計測する。
  // STDDEV(score_total) が信念分布の広がり（entropy spread）の代理指標。
  //
  // attractor_status の閾値:
  //   < 0.05  → 'stable'     (tight cluster around q*)
  //   < 0.15  → 'converging' (moderate spread, ρ(J) < 1 推定)
  //   ≥ 0.15  → 'diverging'  (wide spread, ρ(J) → 1 警告)
  //
  // floor_violation_rate が高い（> 0.1）場合は attractor_status に関わらず
  // Well-Becoming gate 違反として別途 floorViolationAlert BPMN が発火する。
  // RisingWave 制約（2026-05-07 確認済み）:
  //   - STDDEV() 非対応 → SQRT(E[X^2] - E[X]^2) で手動計算
  //   - COUNT(*) FILTER / SUM() FILTER は MV 内で不可 → CASE WHEN で代替
  //   - AVG() FILTER は MV 内で動作する（scalar/table context のみ不可）
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_attractor_stability AS
    SELECT
      COUNT(*)                                                                     AS total_events,
      SUM(CASE WHEN scored = true THEN 1 ELSE 0 END)                              AS scored_events,
      COUNT(DISTINCT agent_did)                                                    AS n_agents,
      COUNT(DISTINCT case_id)                                                      AS n_callers,

      -- entropy_spread = SQRT(E[X^2] - E[X]^2) ≈ stddev（GREATEST で負数回避）
      SQRT(GREATEST(
        AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
        - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
        * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
        0.0
      ))                                                                           AS entropy_spread,

      AVG(CASE WHEN scored = true THEN score_total        ELSE NULL END)          AS mean_score_total,
      AVG(CASE WHEN scored = true THEN score_spirit       ELSE NULL END)          AS mean_spirit,
      AVG(CASE WHEN scored = true THEN score_wellbecoming ELSE NULL END)          AS mean_wellbecoming,
      AVG(CASE WHEN scored = true THEN score_feeling      ELSE NULL END)          AS mean_feeling,
      AVG(CASE WHEN scored = true THEN score_buffer       ELSE NULL END)          AS mean_buffer,
      AVG(CASE WHEN separation_delta IS NOT NULL THEN separation_delta ELSE NULL END) AS mean_separation_delta,

      CAST(SUM(CASE WHEN floor_violated = true THEN 1 ELSE 0 END) AS FLOAT) /
        NULLIF(SUM(CASE WHEN scored = true THEN 1 ELSE 0 END), 0)                 AS floor_violation_rate,

      -- attractor_status: ρ(J) < 1 の代理指標
      --   spread < 0.05  → 'stable'     (tight cluster around q*)
      --   spread < 0.15  → 'converging' (ρ(J) < 1 推定)
      --   spread ≥ 0.15  → 'diverging'  (ρ(J) → 1 警告)
      CASE
        WHEN SQRT(GREATEST(
               AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
               - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
               * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
               0.0
             )) < 0.05 THEN 'stable'
        WHEN SQRT(GREATEST(
               AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
               - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
               * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
               0.0
             )) < 0.15 THEN 'converging'
        ELSE 'diverging'
      END                                                                          AS attractor_status,

      MAX(created_at)                                                              AS last_event_at
    FROM vertex_wellbecoming_event
  `.execute(db);

  // ── mv_attractor_stability_by_agent ─────────────────────────────────────
  // agent ごとの信念収束度。特定 agent の entropy_spread が高い場合は
  // その agent の W_ij（信頼重み）または観測品質を調査する。
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_attractor_stability_by_agent AS
    SELECT
      agent_did,
      SUM(CASE WHEN scored = true THEN 1 ELSE 0 END)                              AS scored_events,
      SQRT(GREATEST(
        AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
        - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
        * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
        0.0
      ))                                                                           AS entropy_spread,
      AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)                 AS mean_score_total,
      AVG(CASE WHEN separation_delta IS NOT NULL THEN separation_delta ELSE NULL END) AS mean_separation_delta,
      SUM(CASE WHEN floor_violated = true THEN 1 ELSE 0 END)                      AS floor_violations,
      CASE
        WHEN SQRT(GREATEST(
               AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
               - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
               * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
               0.0
             )) < 0.05 THEN 'stable'
        WHEN SQRT(GREATEST(
               AVG(CASE WHEN scored = true THEN score_total * score_total ELSE NULL END)
               - AVG(CASE WHEN scored = true THEN score_total ELSE NULL END)
               * AVG(CASE WHEN scored = true THEN score_total ELSE NULL END),
               0.0
             )) < 0.15 THEN 'converging'
        ELSE 'diverging'
      END                                                                          AS attractor_status,
      MAX(created_at)                                                              AS last_event_at
    FROM vertex_wellbecoming_event
    GROUP BY agent_did
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_attractor_stability_by_agent`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_attractor_stability`.execute(db);
}
