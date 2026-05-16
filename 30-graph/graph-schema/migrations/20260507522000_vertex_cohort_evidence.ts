import { Kysely, sql } from 'kysely';

// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_cohort_evidence (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      rkey VARCHAR,
      repo VARCHAR,
      collection VARCHAR,
      cohort_did VARCHAR,
      evidence_hash VARCHAR,
      signal_kind VARCHAR,
      posterior DOUBLE PRECISION,
      judge_agreement BOOLEAN,
      tier VARCHAR,
      observed_at VARCHAR,
      evidence_payload TEXT,
      actor_did VARCHAR,
      org_did VARCHAR
    )
  `.execute(db);

  await sql`
    INSERT INTO vertex_cohort_evidence (
      vertex_id, created_date, sensitivity_ord, owner_did, rkey, repo, collection,
      cohort_did, evidence_hash, signal_kind, posterior, judge_agreement, tier,
      observed_at, actor_did, org_did
    )
    SELECT
      concat('evidence:', evidence_hash),
      CAST(NULL AS DATE),
      1,
      repo,
      rkey,
      repo,
      collection,
      cohort_did,
      evidence_hash,
      signal_kind,
      posterior,
      judge_agreement,
      tier,
      observed_at,
      actor_did,
      org_did
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.cohort.evidence'
      AND evidence_hash IS NOT NULL
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cohort_k_drift`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cohort_identity_posterior`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cohort_identity_posterior AS
    SELECT
      cohort_did,
      COUNT(*)::BIGINT AS evidence_count,
      AVG(posterior)::DOUBLE PRECISION AS avg_posterior,
      MAX(posterior)::DOUBLE PRECISION AS max_posterior,
      SUM(CASE WHEN judge_agreement THEN 1 ELSE 0 END)::BIGINT AS judge_agree_count,
      SUM(CASE WHEN posterior > 0.95 AND judge_agreement THEN 1 ELSE 0 END)::BIGINT AS fission_ready_count,
      MAX(observed_at) AS last_evidence_at
    FROM vertex_cohort_evidence
    GROUP BY cohort_did
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cohort_k_drift AS
    SELECT
      cohort_did,
      COUNT(DISTINCT signal_kind)::BIGINT AS distinct_signal_kinds,
      COUNT(*)::BIGINT AS evidence_count,
      CASE WHEN COUNT(DISTINCT signal_kind) = 0 THEN 0
           ELSE COUNT(*) / COUNT(DISTINCT signal_kind)
      END::BIGINT AS k_proxy
    FROM vertex_cohort_evidence
    GROUP BY cohort_did
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cohort_k_drift`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_cohort_identity_posterior`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_cohort_evidence`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cohort_identity_posterior AS
    SELECT
      cohort_did,
      COUNT(*)::BIGINT AS evidence_count,
      AVG(posterior)::DOUBLE PRECISION AS avg_posterior,
      MAX(posterior)::DOUBLE PRECISION AS max_posterior,
      SUM(CASE WHEN judge_agreement THEN 1 ELSE 0 END)::BIGINT AS judge_agree_count,
      SUM(CASE WHEN posterior > 0.95 AND judge_agreement THEN 1 ELSE 0 END)::BIGINT AS fission_ready_count,
      MAX(observed_at) AS last_evidence_at
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.cohort.evidence'
    GROUP BY cohort_did
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_cohort_k_drift AS
    SELECT
      cohort_did,
      COUNT(DISTINCT signal_kind)::BIGINT AS distinct_signal_kinds,
      COUNT(*)::BIGINT AS evidence_count,
      CASE WHEN COUNT(DISTINCT signal_kind) = 0 THEN 0
           ELSE COUNT(*) / COUNT(DISTINCT signal_kind)
      END::BIGINT AS k_proxy
    FROM vertex_repo_record
    WHERE collection = 'ai.gftd.cohort.evidence'
    GROUP BY cohort_did
  `.execute(db);
}
