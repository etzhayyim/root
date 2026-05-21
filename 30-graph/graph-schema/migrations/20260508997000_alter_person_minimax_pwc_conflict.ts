import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Add pwc_conflict_violated axis to vertex_etzhayyim_person_minimax.
 *
 * Rationale (2026-05-08): C1 (監査法人 vertical SaaS) was scored regret 0.28
 * and recommended `assign`, but a CEO concurrent-employment review caught
 * a PwC conflict and the candidate was hard-blocked.
 *
 * pwc_conflict_violated treats Big4 audit/consulting/tax/audit-adjacent
 * SaaS scope as a Spirit floor violation when CEO j-kawasaki is in champion
 * role. Independent of regret_score and ip_leak_risk because conflict-of-
 * interest sits at a different ethical axis (legal + contractual obligation
 * to PwC) — must be evaluated even when the deal is otherwise low-risk.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const existing = await sql<{ column_name: string }>`
    SELECT column_name FROM information_schema.columns
    WHERE table_name = 'vertex_etzhayyim_person_minimax'
  `.execute(db);
  const have = new Set(existing.rows.map((r: any) => r.column_name));
  if (!have.has('pwc_conflict_violated')) {
    await sql`ALTER TABLE vertex_etzhayyim_person_minimax ADD COLUMN pwc_conflict_violated boolean DEFAULT false`.execute(db);
  }
  if (!have.has('conflict_scope')) {
    await sql`ALTER TABLE vertex_etzhayyim_person_minimax ADD COLUMN conflict_scope varchar`.execute(db);
  }

  // Replace MV to surface pwc_conflict_violated rows excluded from top picks
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_minimax_top_assignments`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_minimax_top_assignments AS
    SELECT
      decision_kind,
      candidate_target,
      person_did,
      regret_score,
      worst_case_loss_jpy,
      expected_value_jpy,
      spirit_floor_violated,
      pwc_conflict_violated,
      ip_leak_risk,
      recommendation,
      assessed_at
    FROM vertex_etzhayyim_person_minimax
    WHERE spirit_floor_violated = false
      AND pwc_conflict_violated = false
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_etzhayyim_minimax_top_assignments`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_etzhayyim_minimax_top_assignments AS
    SELECT
      decision_kind, candidate_target, person_did, regret_score,
      worst_case_loss_jpy, expected_value_jpy, spirit_floor_violated,
      ip_leak_risk, recommendation, assessed_at
    FROM vertex_etzhayyim_person_minimax
    WHERE spirit_floor_violated = false
  `.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_person_minimax DROP COLUMN conflict_scope`.execute(db);
  await sql`ALTER TABLE vertex_etzhayyim_person_minimax DROP COLUMN pwc_conflict_violated`.execute(db);
}
