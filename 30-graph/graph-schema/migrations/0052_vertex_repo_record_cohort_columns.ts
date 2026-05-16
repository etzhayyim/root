import { Kysely, sql } from 'kysely';

/**
 * Migration 0052: cohort evidence promoted columns on vertex_repo_record.
 *
 * ADR-0026 Phase B: `ai.gftd.cohort.evidence` records land in
 * `vertex_repo_record` via PDS commit pipeline. These 7 scalar columns
 * (promoted per graph-schema CLAUDE.md §Schema Design) back the 2 MVs
 * created in migration 0034 (`mv_cohort_identity_posterior`,
 * `mv_cohort_k_drift`).
 *
 * Column mapping (lexicon path → SQL column):
 *   $.cohortDid         → cohort_did         VARCHAR(512)
 *   $.evidenceHash      → evidence_hash      VARCHAR(128)
 *   $.signalKind        → signal_kind        VARCHAR(128)
 *   $.posterior         → posterior          DOUBLE PRECISION
 *   $.judgeAgreement    → judge_agreement    BOOLEAN
 *   $.tier              → tier               VARCHAR(32)
 *   $.observedAt        → observed_at        VARCHAR(64)
 *
 * The 4 signature/fission columns (segment_hash, k_anonymity,
 * fission_enabled, derived_from) live on `vertex_cohort_actor`
 * (created in migration 0036 — next iteration).
 *
 * Insert allowlist: already extended in
 * `50-infra/cloudflare/workers/atproto/src/insert-columns.ts` (Iteration 3).
 *
 * Pre-flight: vertex_repo_record is large (commit log) but this is ADD COLUMN
 * only (no backfill / no index) — O(1) schema op.
 */
export async function up(db: Kysely<any>): Promise<void> {
  const existing = await sql<{ column_name: string }>`
    SELECT column_name
    FROM information_schema.columns
    WHERE table_name = 'vertex_repo_record'
      AND column_name IN (
        'cohort_did',
        'evidence_hash',
        'signal_kind',
        'posterior',
        'judge_agreement',
        'tier',
        'observed_at'
      )
  `.execute(db);
  const cols = new Set(existing.rows.map((row) => row.column_name));

  if (!cols.has('cohort_did')) {
    await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" ADD COLUMN "cohort_did" VARCHAR`.compile(db));
  }
  if (!cols.has('evidence_hash')) {
    await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" ADD COLUMN "evidence_hash" VARCHAR`.compile(db));
  }
  if (!cols.has('signal_kind')) {
    await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" ADD COLUMN "signal_kind" VARCHAR`.compile(db));
  }
  if (!cols.has('posterior')) {
    await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" ADD COLUMN "posterior" DOUBLE PRECISION`.compile(db));
  }
  if (!cols.has('judge_agreement')) {
    await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" ADD COLUMN "judge_agreement" BOOLEAN`.compile(db));
  }
  if (!cols.has('tier')) {
    await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" ADD COLUMN "tier" VARCHAR`.compile(db));
  }
  if (!cols.has('observed_at')) {
    await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" ADD COLUMN "observed_at" VARCHAR`.compile(db));
  }
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "cohort_did"`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "evidence_hash"`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "signal_kind"`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "posterior"`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "judge_agreement"`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "tier"`.compile(db));
  await db.executeQuery(sql`ALTER TABLE "vertex_repo_record" DROP COLUMN IF EXISTS "observed_at"`.compile(db));
}
