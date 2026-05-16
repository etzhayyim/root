import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0098 Repo-as-Attractor — W_ij 動的更新 + Bounded Confidence (C).
//
// SBGE の信頼重み W_ij を永続化するテーブル。
// wellbecoming.trust.updateWeights タスクが mv_attractor_stability_by_agent から
// 信念距離 D(q_i, q_j) を計算し、Bounded Confidence フィルタ（ε）を適用して
// weight を upsert する。
//
// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS edge_trust_weight (
      edge_id     VARCHAR PRIMARY KEY,   -- '{src_did}→{dst_did}'
      src_did     VARCHAR NOT NULL,       -- W_ij の i（信頼する主体）
      dst_did     VARCHAR NOT NULL,       -- W_ij の j（信頼される主体）

      -- W_ij ∈ [0,1]  exp(-k * distance)  当 distance < bc_epsilon, else 0
      weight      DOUBLE PRECISION NOT NULL DEFAULT 1.0,

      -- 信念距離 D(q_i, q_j) = |mean_score_i - mean_score_j|  (0 if no data)
      distance    DOUBLE PRECISION NOT NULL DEFAULT 0.0,

      -- Bounded Confidence 閾値 ε（この距離以上 → blocked = true, weight = 0）
      bc_epsilon  DOUBLE PRECISION NOT NULL DEFAULT 0.3,

      -- blocked = true のとき SBGE での W_ij = 0（信念伝播を遮断）
      blocked     BOOLEAN NOT NULL DEFAULT false,

      updated_at  TIMESTAMP NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_etw_src ON edge_trust_weight (src_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_etw_dst ON edge_trust_weight (dst_did)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_etw_blocked ON edge_trust_weight (blocked, weight)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS edge_trust_weight`.execute(db);
}
