import { Kysely, sql } from 'kysely';

/**
 * Migration 0054: cohort identity posterior + k-drift MVs (ADR-0026 Iteration 3).
 *
 * Drives:
 *   1. Fission decision (`posterior > 0.95 AND judge_agreement`) for
 *      `app.etzhayyim.cohort.fission` procedure.
 *   2. k-anonymity drift detection for Path F scheduler middleware
 *      `cohortKReevaluate` task.
 *
 * Source collection: `app.etzhayyim.cohort.evidence` (Tier 1 hashed AT Repo record).
 *
 * Pre-flight (graph-schema CLAUDE.md §MV Memory Safety Guardrails):
 *   - GROUP BY cohort_did cardinality: 初期 ~31、scale ~10k → safe
 *   - Backfill rowcount: 0 (collection 新設、過去 row なし) → safe
 *   - MAX(varchar) 列数: 0 → safe
 *   - Narrow MV (keys + numeric aggregates only) → safe
 *
 * Design: `90-docs/260414-cohort-identity-posterior-mv-draft.md`
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cohort_identity_posterior AS
    SELECT
      cohort_did,
      COUNT(*)::BIGINT                                              AS evidence_count,
      AVG(posterior)::DOUBLE PRECISION                              AS avg_posterior,
      MAX(posterior)::DOUBLE PRECISION                              AS max_posterior,
      SUM(CASE WHEN judge_agreement THEN 1 ELSE 0 END)::BIGINT      AS judge_agree_count,
      SUM(CASE WHEN posterior > 0.95 AND judge_agreement
               THEN 1 ELSE 0 END)::BIGINT                           AS fission_ready_count,
      MAX(observed_at)                                              AS last_evidence_at
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.cohort.evidence'
    GROUP BY cohort_did`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cohort_k_drift AS
    SELECT
      cohort_did,
      COUNT(DISTINCT signal_kind)::BIGINT AS distinct_signal_kinds,
      COUNT(*)::BIGINT                    AS evidence_count,
      CASE WHEN COUNT(DISTINCT signal_kind) = 0 THEN 0
           ELSE COUNT(*) / COUNT(DISTINCT signal_kind)
      END::BIGINT                         AS k_proxy
    FROM vertex_repo_record
    WHERE collection = 'app.etzhayyim.cohort.evidence'
    GROUP BY cohort_did`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cohort_k_drift`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cohort_identity_posterior`.execute(db);
}
